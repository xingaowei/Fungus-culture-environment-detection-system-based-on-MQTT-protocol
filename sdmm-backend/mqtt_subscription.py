# mqtt_subscription.py

import struct
import threading
import time
import uuid
from datetime import datetime

import paho.mqtt.client as mqtt
import requests
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SUBSCRIPTION_FILE_PATH = 'subscriptions.yaml'
API_BASE_URL = 'http://localhost:5000/api'


def load_subscription_config():
    with open(SUBSCRIPTION_FILE_PATH, 'r') as file:
        return yaml.safe_load(file)


class SubscriptionManager:
    def __init__(self):
        self.subscriptions = {}
        self.lock = threading.Lock()

    def start(self):
        config = load_subscription_config()
        if config['subscriptions'] is not None:
            for sub in config['subscriptions']:
                self.add_subscription(sub)

    def add_subscription(self, subscription):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if subscription.get('username') and subscription.get('password'):
            client.username_pw_set(subscription['username'], subscription['password'])

        def on_connect(_client, userdata, flags, rc, properties=None):
            _client.subscribe(subscription['topic'])

        client.on_connect = on_connect
        client.on_message = lambda _client, userdata, msg: self.handle_message(subscription, msg)

        # Implement retry mechanism with exponential backoff
        max_retries = 100
        retry_count = 0
        backoff_time = 2  # Start with 2 seconds

        while retry_count < max_retries:
            try:
                client.connect(subscription['broker_address'], subscription['broker_port'], 60)
                break  # If connection is successful, exit the loop
            except ConnectionRefusedError:
                retry_count += 1
                print_colored(f"Connection to {subscription['broker_address']}:{subscription['broker_port']} refused. "
                              f"Retrying {retry_count}/{max_retries} after {backoff_time} seconds...", "43")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
        else:
            print_colored(f"Failed to connect to {subscription['broker_address']}:{subscription['broker_port']} after "
                          f"{max_retries} attempts. Skipping this subscription.", "41")
            return

        # Register subscription but don't update database until message is received
        self.subscriptions[subscription['sensor_name']] = {
            'client': client,
            'broker_address': subscription['broker_address'],
            'broker_port': subscription['broker_port'],
            'topic': subscription['topic'],
            'username': subscription.get('username'),
            'password': subscription.get('password'),
            'sensor_types': subscription.get('sensor_types'),
            'metadata': subscription.get('metadata', {}),
            'last_message_time': time.time(),
            'threshold': 10,  # Default threshold 10s
            'sensor_id': None,
            'status': 'normal'
        }

        threading.Thread(target=client.loop_forever).start()

    def remove_subscription(self, sensor_name):
        if sensor_name in self.subscriptions:
            subscription = self.subscriptions[sensor_name]
            sensor_id = subscription['sensor_id']

            # Disconnect the MQTT client
            if subscription['client'].is_connected():
                subscription['client'].disconnect()
                subscription['client'].loop_stop()
                print_colored(f'Disconnected from {subscription["broker_address"]}', "42")
            else:
                print_colored('Failed to disconnect from MQTT broker: not connected.', "41")
            time.sleep(1)  # Avoid ongoing msg handling

            self.remove_sensor_from_db(sensor_id)

            del self.subscriptions[sensor_name]

    @staticmethod
    def remove_sensor_from_db(sensor_id):
        # Update Sensors table (mark as deleted)
        requests.delete(f'{API_BASE_URL}/sensors/{sensor_id}/delete')
        # Update SensorMetadata table (mark as deleted)
        response = requests.get(f'{API_BASE_URL}/metadata/sensor/{sensor_id}')
        if response.status_code == 200:
            metadata_list = response.json()
            for metadata in metadata_list:
                requests.delete(f'{API_BASE_URL}/metadata/{metadata["metadata_id"]}')
        # Update the SensorStatusHistory table
        status_history_data = {
            'status': 'disabled',
        }
        requests.put(f'{API_BASE_URL}/sensors/{sensor_id}/status', json=status_history_data)

    def handle_message(self, subscription, msg):
        # Update the last message time for the sensor
        self.subscriptions[subscription['sensor_name']]['last_message_time'] = time.time()

        try:
            device_id, timestamp, temperature, humidity, co2_concentration = struct.unpack('!16sQiII', msg.payload)

            sensor_id = str(uuid.UUID(bytes=device_id))
            timestamp = datetime.fromtimestamp(timestamp)
            temperature = temperature / 100.0
            humidity = float(humidity)
            co2_concentration = float(co2_concentration)

            # msg with new sensor_id
            response = requests.get(f'{API_BASE_URL}/sensors/{sensor_id}')
            if response.status_code == 404:
                if self.subscriptions[subscription['sensor_name']]['sensor_id']:
                    old_sensor_id = self.subscriptions[subscription['sensor_name']]['sensor_id']
                    self.remove_sensor_from_db(old_sensor_id)
                self.subscriptions[subscription['sensor_name']]['sensor_id'] = sensor_id
                self.add_sensor_to_db(sensor_id, subscription)

            # re-connected
            if self.subscriptions[subscription['sensor_name']]['status'] == 'offline':
                self.subscriptions[subscription['sensor_name']]['status'] = 'normal'
                print_colored(
                    f"Sensor {subscription['sensor_name']} (ID: {sensor_id}) has received new data. "
                    f"Marking as normal.", "44")
                self.update_sensor_status(sensor_id, 'normal')

            sensor_data = {
                'sensor_id': sensor_id,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sensor_data': [
                    {'type_id': self.get_type_id('Temperature'), 'value': temperature},
                    {'type_id': self.get_type_id('Humidity'), 'value': humidity},
                    {'type_id': self.get_type_id('CO2 Concentration'), 'value': co2_concentration}
                ]
            }

            # Send data to the API for storage
            for data in sensor_data['sensor_data']:
                data_payload = {
                    'sensor_id': sensor_data['sensor_id'],
                    'type_id': data['type_id'],
                    'timestamp': sensor_data['timestamp'],
                    'value': data['value']
                }
                requests.post(f'{API_BASE_URL}/data', json=data_payload)

        except struct.error as e:
            print_colored(f"Failed to unpack MQTT message: {e}", "41")
        except Exception as e:
            print_colored(f"Failed to handle message: {e}", "41")

    def add_sensor_to_db(self, sensor_id, subscription):
        # Add sensor to Sensors table
        sensor_data = {
            'sensor_id': sensor_id,
            'name': subscription['sensor_name'],
            'location': subscription['topic'],
            'status': 'active'
        }
        requests.post(f'{API_BASE_URL}/sensors', json=sensor_data)

        # Add mappings to SensorTypeMapping table
        for sensor_type in subscription['sensor_types']:
            mapping_data = {
                'sensor_id': sensor_id,
                'type_id': self.get_type_id(sensor_type)
            }
            requests.post(f'{API_BASE_URL}/mappings', json=mapping_data)

        # Add metadata to SensorMetadata table
        if 'metadata' in subscription:
            metadata = subscription['metadata']
            for item in metadata:
                key, value = list(item.items())[0]
                metadata_payload = {
                    'sensor_id': sensor_id,
                    'key': key,
                    'value': value
                }
                requests.post(f'{API_BASE_URL}/metadata', json=metadata_payload)

        # Update the SensorStatusHistory table
        status_history_data = {
            'status': 'normal',
        }
        requests.put(f'{API_BASE_URL}/sensors/{sensor_id}/status', json=status_history_data)

    def monitor_sensors(self):
        while True:
            current_time = time.time()
            for sensor_name, data in list(self.subscriptions.items()):
                sensor_id = data.get('sensor_id')
                status = self.get_latest_sensor_status(sensor_id)
                if status != 'offline':
                    if sensor_id and (current_time - data['last_message_time'] > data['threshold']):
                        print_colored(
                            f"Sensor {sensor_name} (ID: {sensor_id}) has not received data within the threshold. "
                            f"Marking as offline.", "44")
                        alert_payload = {
                            'sensor_id': sensor_id,
                            'alert_type': 'connection issue',
                            'message': f'Sensor {sensor_name} has not received data within the threshold.',
                        }
                        response = requests.post(f'{API_BASE_URL}/alerts', json=alert_payload)
                        if response.status_code not in [201]:
                            raise Exception('Failed to send alerts')
                        with self.lock:
                            self.subscriptions[sensor_name]['status'] = 'offline'
                        self.update_sensor_status(sensor_id, 'offline')
            time.sleep(5)  # Check every 5 seconds

    @staticmethod
    def update_sensor_status(sensor_id, status):
        requests.put(f'{API_BASE_URL}/sensors/{sensor_id}/status', json={'status': status})

    @staticmethod
    def get_latest_sensor_status(sensor_id):
        response = requests.get(f'{API_BASE_URL}/sensors/{sensor_id}/latest_status')
        if response.status_code != 200:
            return None
        latest_status = response.json()['status']
        if latest_status:
            return latest_status
        return None

    @staticmethod
    def get_type_id(type_name):
        # Logic to get the type_id from API or local cache
        response = requests.get(f'{API_BASE_URL}/types/name/{type_name}')
        return response.json()['type_id']

    def reload_config(self):
        new_config = load_subscription_config()
        if new_config is None:
            new_config = {'subscriptions': []}
        new_subscriptions = {sub['sensor_name']: sub for sub in new_config['subscriptions']}

        # Detect removed subscriptions
        for sensor_name in list(self.subscriptions.keys()):
            if sensor_name not in new_subscriptions:
                print_colored(f"Removing subscription for {sensor_name}", "44")
                self.remove_subscription(sensor_name)

        # Detect new or updated subscriptions
        for sensor_name, new_sub in new_subscriptions.items():
            if sensor_name not in self.subscriptions:
                print_colored(f"Adding new subscription for {sensor_name}", "44")
                self.add_subscription(new_sub)
            else:
                existing_sub = self.subscriptions[sensor_name]
                if (new_sub['broker_address'] != existing_sub['broker_address'] or
                        new_sub['broker_port'] != existing_sub['broker_port'] or
                        new_sub['topic'] != existing_sub['topic'] or
                        new_sub['sensor_types'] != existing_sub['sensor_types'] or
                        (new_sub.get('metadata') or {}) != (existing_sub.get('metadata') or {})):
                    print_colored(f"Updating subscription for {sensor_name}", "44")
                    self.remove_subscription(sensor_name)
                    self.add_subscription(new_sub)


class ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, _manager):
        self.manager = _manager

    def on_modified(self, event):
        if event.src_path.endswith(SUBSCRIPTION_FILE_PATH):
            print_colored("Config file changed, reloading subscriptions...", "44")
            with self.manager.lock:
                self.manager.reload_config()


def print_colored(_text, color_code):
    _text = "[MQTT_SYS] - " + _text
    print(f"\033[{color_code}m{_text}\033[0m", flush=True)


if __name__ == '__main__':
    manager = SubscriptionManager()
    manager.start()
    threading.Thread(target=manager.monitor_sensors).start()

    # Set up file system event handler to monitor the config file
    event_handler = ConfigFileEventHandler(manager)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

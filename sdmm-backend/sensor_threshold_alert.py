# sensor_threshold_alert.py

import threading
import time
from datetime import datetime, timedelta

import requests
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SUBSCRIPTION_FILE_PATH = 'subscriptions.yaml'
API_BASE_URL = 'http://localhost:5000/api'

AVE_TIME_RANGE_THRESHOLD = 60
CHECK_INTERVAL = 60
TIME_LAG = 0


def load_subscription_config():
    with open(SUBSCRIPTION_FILE_PATH, 'r') as file:
        return yaml.safe_load(file)


class SensorThresholdAlert:
    def __init__(self):
        self.subscriptions = {}
        self.lock = threading.Lock()
        self.load_config()

    def load_config(self):
        config = load_subscription_config()
        for subscription in config['subscriptions']:
            self.subscriptions[subscription['sensor_name']] = {
                'thresholds': self.extract_thresholds(subscription.get('metadata', {}))
            }

    @staticmethod
    def extract_thresholds(metadata):
        thresholds = {}
        for item in metadata:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key == 'thresholds':
                        for sensor_type, limits in value.items():
                            for limit_key, limit_value in limits.items():
                                # Construct a threshold key like "Temperature_min"
                                threshold_key = f"{sensor_type}_{limit_key}"
                                thresholds[threshold_key] = limit_value
        return thresholds

    def monitor_sensors(self):
        while True:
            with self.lock:
                for sensor_name, data in self.subscriptions.items():
                    sensor_data = self.get_sensor_data(sensor_name, AVE_TIME_RANGE_THRESHOLD)
                    if sensor_data:
                        self.evaluate_thresholds(sensor_name, sensor_data, data['thresholds'])
            time.sleep(CHECK_INTERVAL)  # Check every 60 seconds

    def get_sensor_data(self, sensor_name, time_range):
        now = datetime.now()
        start_time = (now - timedelta(seconds=time_range) + timedelta(hours=TIME_LAG)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (now + timedelta(hours=TIME_LAG)).strftime('%Y-%m-%d %H:%M:%S')
        sensor_id = self.get_sensor_id(sensor_name)
        if sensor_id is None:
            return None

        type_ids = {
            'Temperature': self.get_type_id('Temperature'),
            'Humidity': self.get_type_id('Humidity'),
            'CO2 Concentration': self.get_type_id('CO2 Concentration')
        }

        sensor_data = {}
        for sensor_type, type_id in type_ids.items():
            response = requests.get(f'{API_BASE_URL}/data', params={
                'sensor_id': sensor_id,
                'type_id': type_id,
                'start_time': start_time,
                'end_time': end_time
            })
            if response.status_code == 200:
                data = response.json()
                if data:
                    sensor_data[sensor_type] = sum(d['value'] for d in data) / len(data)

        return sensor_data

    @staticmethod
    def get_type_id(type_name):
        response = requests.get(f'{API_BASE_URL}/types/name/{type_name}')
        if response.status_code == 200:
            return response.json()['type_id']
        return None

    def evaluate_thresholds(self, sensor_name, sensor_data, thresholds):
        alerts = []
        alert_type = "threshold breach"  # This is a descriptive alert type
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp

        for sensor_type, average_value in sensor_data.items():
            min_key = f"{sensor_type}_min"
            max_key = f"{sensor_type}_max"
            if min_key in thresholds and average_value < thresholds[min_key]:
                alerts.append(f"{sensor_type} below minimum threshold: {average_value:.2f} < {thresholds[min_key]}")
            if max_key in thresholds and average_value > thresholds[max_key]:
                alerts.append(f"{sensor_type} above maximum threshold: {average_value:.2f} > {thresholds[max_key]}")

        if alerts:
            self.trigger_alert(timestamp, sensor_name, alert_type, alerts)
            self.update_sensor_status(sensor_name, 'warning')
        else:
            self.update_sensor_status(sensor_name, 'normal')

    def trigger_alert(self, timestamp, sensor_name, alert_type, alerts):
        # Placeholder for alert triggering logic, e.g., sending an email or push notification
        for alert in alerts:
            print_colored(f'[{timestamp}] ALERT: {sensor_name} - {alert_type} - {alert}', '43')
            alert_payload = {
                'sensor_id': self.get_sensor_id(sensor_name),
                'alert_type': alert_type,
                'message': alert,
            }
            response = requests.post(f'{API_BASE_URL}/alerts', json=alert_payload)
            if response.status_code not in [201]:
                raise (Exception('Alert send failed'))

    def update_sensor_status(self, sensor_name, status):
        sensor_id = self.get_sensor_id(sensor_name)
        if sensor_id:
            sensor = requests.get(f'{API_BASE_URL}/sensors/{sensor_id}').json()
            if sensor['status'] != 'deleted':
                status_data = {'status': status}
                requests.put(f'{API_BASE_URL}/sensors/{sensor_id}/status', json=status_data)

    @staticmethod
    def get_sensor_id(sensor_name):
        response = requests.get(f'{API_BASE_URL}/sensors/sensor_id', params={'sensor_name': sensor_name})
        if response.status_code == 200 and response.json():
            return response.json()['sensor_id']
        return None

    def reload_config(self):
        with self.lock:
            self.subscriptions = {}
            self.load_config()
            print_colored("Config reloaded.", '42')


class ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, _monitor):
        self.monitor = _monitor

    def on_modified(self, event):
        if event.src_path.endswith(SUBSCRIPTION_FILE_PATH):
            print_colored("Subscription file changed, reloading thresholds...", '44')
            self.monitor.reload_config()


def print_colored(_text, color_code):
    _text = "[ALERT_SYS] - " + _text
    print(f"\033[{color_code}m{_text}\033[0m", flush=True)


if __name__ == '__main__':
    monitor = SensorThresholdAlert()
    threading.Thread(target=monitor.monitor_sensors).start()

    # Set up file system event handler to monitor the config file
    event_handler = ConfigFileEventHandler(monitor)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

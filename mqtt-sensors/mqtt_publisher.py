# Filename: mqtt_publisher.py

import os
import time
import uuid
import random
import struct
import paho.mqtt.client as mqtt
from datetime import datetime

mqtt_server = os.getenv('MQTT_SERVER', 'localhost')
mqtt_port = int(os.getenv('MQTT_PORT', 1883))
mqtt_topic = os.getenv('MQTT_TOPIC', 'sensor/data')
publish_interval = int(os.getenv('PUBLISH_INTERVAL', 1))

device_id = uuid.uuid4()

temperature = random.uniform(0.00, 25.00)
humidity = random.uniform(40.0, 60.0)
co2_concentration = random.uniform(350.0, 450.0)


def generate_sensor_data():
    global temperature, humidity, co2_concentration

    temperature += random.uniform(-0.50, 0.50)
    temperature = max(-10.00, min(40.00, temperature))

    humidity += random.uniform(-1.5, 1.5)
    humidity = max(20.0, min(80.0, humidity))

    co2_concentration += random.uniform(-10.0, 10.0)
    co2_concentration = max(300.0, min(500.0, co2_concentration))

    return int(temperature * 100), int(humidity), int(co2_concentration)


def serialize_data(device_id, timestamp, temperature, humidity, co2_concentration):
    return struct.pack('!16sQiII', device_id.bytes, timestamp, temperature, humidity, co2_concentration)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(mqtt_server, mqtt_port, 60)

while True:
    timestamp = int(time.time())
    temperature_t, humidity_t, co2_concentration_t = generate_sensor_data()
    payload = serialize_data(device_id, timestamp,
                             temperature_t, humidity_t, co2_concentration_t)
    client.publish(mqtt_topic, payload)
    time.sleep(publish_interval)

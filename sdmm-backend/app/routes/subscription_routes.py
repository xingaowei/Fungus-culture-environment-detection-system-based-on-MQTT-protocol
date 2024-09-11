# app/routes/subscription_routes.py

import os

import yaml
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

subscription_bp = Blueprint('subscription_bp', __name__)

SUBSCRIPTION_FILE_PATH = 'subscriptions.yaml'


def load_subscription_config():
    if not os.path.exists(SUBSCRIPTION_FILE_PATH):
        return {'subscriptions': []}

    with open(SUBSCRIPTION_FILE_PATH, 'r') as file:
        return yaml.safe_load(file)


def save_subscription_config(config):
    try:
        os.remove(SUBSCRIPTION_FILE_PATH)
    except FileNotFoundError:
        pass
    with open(SUBSCRIPTION_FILE_PATH, 'w') as file:
        yaml.safe_dump(config, file)


@subscription_bp.route('/api/subscriptions', methods=['GET'])
def get_all_subscriptions():
    config = load_subscription_config()
    return jsonify(config['subscriptions']), 200


@subscription_bp.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    data = request.json

    new_subscription = {
        'broker_address': data['broker_address'],
        'broker_port': data['broker_port'],
        'topic': data['topic'],
        'username': data.get('username'),
        'password': data.get('password'),
        'sensor_types': data['sensor_types'],
        'sensor_name': data['sensor_name'],
        'metadata': data.get('metadata'),
    }

    config = load_subscription_config()

    if config['subscriptions']:
        for subscription in config['subscriptions']:
            if subscription['sensor_name'] == new_subscription['sensor_name']:
                return jsonify({'error': 'Sensor name already exists'}), 409

        for subscription in config['subscriptions']:
            if (subscription['broker_address'] == new_subscription['broker_address'] and
                    subscription['broker_port'] == new_subscription['broker_port'] and
                    subscription['topic'] == new_subscription['topic']):
                return jsonify({'error': 'Subscription with the same broker, port, and topic already exists'}), 409
    else:
        config['subscriptions'] = []
    config['subscriptions'].append(new_subscription)
    save_subscription_config(config)

    return jsonify({'message': 'Subscription created'}), 201


@subscription_bp.route('/api/subscriptions/<sensor_name>', methods=['PUT'])
def update_subscription(sensor_name):
    data = request.json
    config = load_subscription_config()

    if sensor_name is None:
        return jsonify({'error': 'No sensor name provided'}), 400

    new_sensor_name = data.get('sensor_name')
    if new_sensor_name and new_sensor_name != sensor_name:
        for subscription in config['subscriptions']:
            if subscription['sensor_name'] == new_sensor_name:
                return jsonify({'error': 'Sensor name already exists'}), 409

    subscription_to_update = next(
        (subscription for subscription in config['subscriptions'] if subscription['sensor_name'] == sensor_name), None)

    if subscription_to_update is None:
        return jsonify({'error': 'Subscription not found'}), 404

    subscription_to_update['broker_address'] = data.get('broker_address', subscription_to_update['broker_address'])
    subscription_to_update['broker_port'] = data.get('broker_port', subscription_to_update['broker_port'])
    subscription_to_update['topic'] = data.get('topic', subscription_to_update['topic'])
    subscription_to_update['username'] = data.get('username', subscription_to_update['username'])
    subscription_to_update['password'] = data.get('password', subscription_to_update['password'])
    subscription_to_update['sensor_types'] = data.get('sensor_types', subscription_to_update['sensor_types'])
    subscription_to_update['sensor_name'] = new_sensor_name or subscription_to_update['sensor_name']
    subscription_to_update['metadata'] = data.get('metadata', subscription_to_update.get('metadata'))

    save_subscription_config(config)

    return jsonify({'message': f'Subscription with sensor_name "{sensor_name}" updated successfully'}), 200


@subscription_bp.route('/api/subscriptions/<sensor_name>', methods=['DELETE'])
def delete_subscription(sensor_name):
    config = load_subscription_config()

    subscription_to_delete = None
    for i, subscription in enumerate(config['subscriptions']):
        if subscription['sensor_name'] == sensor_name:
            subscription_to_delete = i
            break

    if subscription_to_delete is None:
        return jsonify({'error': 'Subscription not found'}), 404

    del config['subscriptions'][subscription_to_delete]
    save_subscription_config(config)

    return jsonify({'message': f'Subscription with sensor_name "{sensor_name}" deleted'}), 200


@subscription_bp.route('/api/subscriptions/upload', methods=['POST'])
def upload_subscription_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    if not filename.endswith('.yaml'):
        return jsonify({'error': 'Invalid file type'}), 400

    file.save(SUBSCRIPTION_FILE_PATH)
    return jsonify({'message': 'File uploaded and configuration updated'}), 200


@subscription_bp.route('/api/subscriptions/download', methods=['GET'])
def download_subscription_file():
    if not os.path.exists(SUBSCRIPTION_FILE_PATH):
        return jsonify({'error': 'Subscription file not found'}), 404

    return send_file('/app/' + SUBSCRIPTION_FILE_PATH, as_attachment=True, download_name='subscriptions.yaml')

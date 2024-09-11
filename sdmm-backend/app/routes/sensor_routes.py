# app/routes/sensor_routes.py

import re

from flask import Blueprint, request, jsonify

from app.models import db, Sensor

sensor_bp = Blueprint('sensor_bp', __name__)


@sensor_bp.route('/api/sensors', methods=['GET'])
def get_sensors():
    if request.args:
        return jsonify({'error': 'This endpoint does not accept query parameters'}), 400

    sensors = Sensor.query.all()
    return jsonify([sensor.to_dict() for sensor in sensors])


@sensor_bp.route('/api/sensors/sensor_id', methods=['GET'])
def get_sensor_id_from_name():
    sensor_name = request.args.get('sensor_name')

    if not sensor_name:
        return jsonify({'error': 'Missing sensor_name parameter'}), 400

    sensor = Sensor.query.filter_by(name=sensor_name, status='active').first()

    if sensor:
        return jsonify({'sensor_id': sensor.sensor_id})
    else:
        return jsonify({'error': 'Sensor not found or inactive'}), 404


@sensor_bp.route('/api/sensors/<sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    sensor = Sensor.query.filter_by(sensor_id=sensor_id, status='active').first()
    if sensor:
        return jsonify(sensor.to_dict())
    else:
        return jsonify({'error': 'Sensor not found or deleted'}), 404


@sensor_bp.route('/api/sensors/<sensor_id>', methods=['PUT'])
def update_sensor_name(sensor_id):
    data = request.json
    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404
    sensor.name = data['name']
    db.session.commit()
    return jsonify(sensor.to_dict())


@sensor_bp.route('/api/sensors/<sensor_id>/deactivate', methods=['PUT'])
def deactivate_sensor(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404
    sensor.status = 'inactive'
    db.session.commit()
    return jsonify(sensor.to_dict())


@sensor_bp.route('/api/sensors/<sensor_id>/activate', methods=['PUT'])
def activate_sensor(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404
    sensor.status = 'active'
    db.session.commit()
    return jsonify(sensor.to_dict())


@sensor_bp.route('/api/sensors/<sensor_id>/delete', methods=['DELETE'])
def delete_sensor(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404
    sensor.status = 'deleted'
    sensor.deleted_at = db.func.current_timestamp()
    db.session.commit()
    return jsonify({'message': 'Sensor marked as deleted'})


def real_delete_sensor(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404
    db.session.delete(sensor)
    db.session.commit()
    return jsonify({'message': 'Sensor deleted'})


@sensor_bp.route('/api/sensors', methods=['POST'])
def create_sensor():
    data = request.json
    sensor_id = data['sensor_id']

    if not is_valid_uuid(sensor_id):
        return jsonify({'error': 'Invalid sensor_id'}), 400

    existing_sensor = Sensor.query.get(sensor_id)
    if existing_sensor is not None:
        if existing_sensor.status == 'active':
            return jsonify({'error': 'Sensor already exists and is active'}), 409

        existing_sensor.name = data.get('name', existing_sensor.name)
        existing_sensor.location = data.get('location', existing_sensor.location)
        existing_sensor.status = data.get('status', existing_sensor.status)
        existing_sensor.deleted_at = None
        db.session.commit()
        return jsonify(existing_sensor.to_dict()), 200

    new_sensor = Sensor(
        sensor_id=sensor_id,
        name=data['name'],
        location=data.get('location', ''),
        status=data.get('status', 'active')
    )
    db.session.add(new_sensor)
    db.session.commit()
    return jsonify(new_sensor.to_dict()), 201


def is_valid_uuid(uuid_to_test, version=4):
    pattern = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
    return pattern.match(uuid_to_test) is not None

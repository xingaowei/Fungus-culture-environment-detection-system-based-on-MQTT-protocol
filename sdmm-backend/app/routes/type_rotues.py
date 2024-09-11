# app/routes/type_routes.py

import uuid

from flask import Blueprint, request, jsonify

from app.models import db, SensorType

type_bp = Blueprint('type_bp', __name__)


@type_bp.route('/api/types', methods=['GET'])
def get_all_sensor_types():
    sensor_types = SensorType.query.all()
    types_list = [{
        'type_id': sensor_type.type_id,
        'type_name': sensor_type.type_name,
        'unit': sensor_type.unit,
        'created_at': sensor_type.created_at
    } for sensor_type in sensor_types]

    return jsonify(types_list), 200


@type_bp.route('/api/types', methods=['POST'])
def create_sensor_type():
    data = request.json

    type_name = data.get('type_name')
    unit = data.get('unit')

    existing_type = SensorType.query.filter_by(type_name=type_name).first()
    if existing_type:
        return jsonify({'error': 'Sensor type name already exists'}), 400

    new_sensor_type = SensorType(
        type_id=uuid.uuid4(),
        type_name=type_name,
        unit=unit
    )

    db.session.add(new_sensor_type)
    db.session.commit()

    return jsonify({'message': 'Sensor type created', 'type_id': new_sensor_type.type_id}), 201


@type_bp.route('/api/types/<type_id>', methods=['PUT'])
def update_sensor_type(type_id):
    data = request.json

    sensor_type = SensorType.query.get(type_id)
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    sensor_type.type_name = data.get('type_name', sensor_type.type_name)
    sensor_type.unit = data.get('unit', sensor_type.unit)

    db.session.commit()

    return jsonify({'message': 'Sensor type updated', 'type_id': sensor_type.type_id}), 200


@type_bp.route('/api/types/<type_id>', methods=['DELETE'])
def delete_sensor_type(type_id):
    sensor_type = SensorType.query.get(type_id)
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    db.session.delete(sensor_type)
    db.session.commit()

    return jsonify({'message': 'Sensor type deleted'}), 200


@type_bp.route('/api/types/<type_id>', methods=['GET'])
def get_sensor_type_by_id(type_id):
    sensor_type = SensorType.query.get(type_id)
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    type_info = {
        'type_id': sensor_type.type_id,
        'type_name': sensor_type.type_name,
        'unit': sensor_type.unit,
        'created_at': sensor_type.created_at
    }

    return jsonify(type_info), 200


@type_bp.route('/api/types/name/<type_name>', methods=['GET'])
def get_type_id_by_name(type_name):
    sensor_type = SensorType.query.filter_by(type_name=type_name).first()
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    return jsonify({'type_id': sensor_type.type_id}), 200

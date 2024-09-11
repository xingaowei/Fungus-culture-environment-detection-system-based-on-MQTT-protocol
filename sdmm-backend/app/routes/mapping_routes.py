# app/routes/mapping_routes.py

import uuid

from flask import Blueprint, request, jsonify

from app.models import db, SensorTypeMapping, Sensor, SensorType

mapping_bp = Blueprint('mapping_bp', __name__)


@mapping_bp.route('/api/mappings', methods=['GET'])
def get_all_mappings():
    mappings = SensorTypeMapping.query.all()
    mappings_list = [{
        'mapping_id': mapping.mapping_id,
        'sensor_id': mapping.sensor_id,
        'type_id': mapping.type_id,
        'created_at': mapping.created_at
    } for mapping in mappings]

    return jsonify(mappings_list), 200


@mapping_bp.route('/api/mappings', methods=['POST'])
def create_mapping():
    data = request.json

    sensor_id = data.get('sensor_id')
    type_id = data.get('type_id')

    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404

    sensor_type = SensorType.query.get(type_id)
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    existing_mapping = SensorTypeMapping.query.filter_by(sensor_id=sensor_id, type_id=type_id).first()
    if existing_mapping:
        return jsonify({'error': 'Mapping already exists'}), 200

    new_mapping = SensorTypeMapping(
        mapping_id=uuid.uuid4(),
        sensor_id=sensor_id,
        type_id=type_id
    )

    db.session.add(new_mapping)
    db.session.commit()

    return jsonify({'message': 'Mapping created', 'mapping_id': new_mapping.mapping_id}), 201


@mapping_bp.route('/api/mappings/<mapping_id>', methods=['DELETE'])
def delete_mapping(mapping_id):
    mapping = SensorTypeMapping.query.get(mapping_id)
    if mapping is None:
        return jsonify({'error': 'Mapping not found'}), 404

    db.session.delete(mapping)
    db.session.commit()

    return jsonify({'message': 'Mapping deleted'}), 200


@mapping_bp.route('/api/mappings/sensor/<sensor_id>', methods=['GET'])
def get_mappings_by_sensor(sensor_id):
    mappings = SensorTypeMapping.query.filter_by(sensor_id=sensor_id).all()
    if not mappings:
        return jsonify({'error': 'No mappings found for the specified sensor'}), 404

    mappings_list = [{
        'mapping_id': mapping.mapping_id,
        'sensor_id': mapping.sensor_id,
        'type_id': mapping.type_id,
        'created_at': mapping.created_at
    } for mapping in mappings]

    return jsonify(mappings_list), 200


@mapping_bp.route('/api/mappings/type/<type_id>', methods=['GET'])
def get_mappings_by_type(type_id):
    mappings = SensorTypeMapping.query.filter_by(type_id=type_id).all()
    if not mappings:
        return jsonify({'error': 'No mappings found for the specified type'}), 404

    mappings_list = [{
        'mapping_id': mapping.mapping_id,
        'sensor_id': mapping.sensor_id,
        'type_id': mapping.type_id,
        'created_at': mapping.created_at
    } for mapping in mappings]

    return jsonify(mappings_list), 200

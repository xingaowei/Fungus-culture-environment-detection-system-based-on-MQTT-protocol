# app/routes/metadata_routes.py

import uuid

from flask import Blueprint, request, jsonify

from app.models import db, SensorMetadata, Sensor

metadata_bp = Blueprint('metadata_bp', __name__)


@metadata_bp.route('/api/metadata', methods=['GET'])
def get_all_metadata():
    metadata_entries = SensorMetadata.query.filter_by(is_deleted=False).all()
    metadata_list = [{
        'metadata_id': entry.metadata_id,
        'sensor_id': entry.sensor_id,
        'key': entry.meta_key,
        'value': entry.meta_value,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at
    } for entry in metadata_entries]

    return jsonify(metadata_list), 200


@metadata_bp.route('/api/metadata', methods=['POST'])
def create_metadata():
    data = request.json

    sensor_id = data.get('sensor_id')
    key = data.get('key')
    value = data.get('value')

    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404

    existing_metadata = SensorMetadata.query.filter_by(sensor_id=sensor_id, meta_key=key, is_deleted=False).first()
    if existing_metadata:
        return jsonify({'error': 'Metadata key already exists for this sensor'}), 400

    new_metadata = SensorMetadata(
        metadata_id=uuid.uuid4(),
        sensor_id=sensor_id,
        meta_key=key,
        meta_value=value
    )

    db.session.add(new_metadata)
    db.session.commit()

    return jsonify({'message': 'Metadata created', 'metadata_id': new_metadata.metadata_id}), 201


@metadata_bp.route('/api/metadata/<metadata_id>', methods=['PUT'])
def update_metadata(metadata_id):
    data = request.json

    metadata = SensorMetadata.query.get(metadata_id)
    if metadata is None or metadata.is_deleted:
        return jsonify({'error': 'Metadata not found'}), 404

    metadata.meta_key = data.get('key', metadata.meta_key)
    metadata.meta_value = data.get('value', metadata.meta_value)
    metadata.updated_at = db.func.current_timestamp()

    db.session.commit()

    return jsonify({'message': 'Metadata updated', 'metadata_id': metadata.metadata_id}), 200


@metadata_bp.route('/api/metadata/<metadata_id>', methods=['DELETE'])
def delete_metadata(metadata_id):
    metadata = SensorMetadata.query.get(metadata_id)
    if metadata is None or metadata.is_deleted:
        return jsonify({'error': 'Metadata not found'}), 404

    metadata.is_deleted = True
    db.session.commit()

    return jsonify({'message': 'Metadata deleted'}), 200


@metadata_bp.route('/api/metadata/sensor/<sensor_id>', methods=['GET'])
def get_metadata_by_sensor(sensor_id):
    metadata_entries = SensorMetadata.query.filter_by(sensor_id=sensor_id, is_deleted=False).all()
    if not metadata_entries:
        return jsonify({'error': 'No metadata found for the specified sensor'}), 404

    metadata_list = [{
        'metadata_id': entry.metadata_id,
        'sensor_id': entry.sensor_id,
        'key': entry.meta_key,
        'value': entry.meta_value,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at
    } for entry in metadata_entries]

    return jsonify(metadata_list), 200

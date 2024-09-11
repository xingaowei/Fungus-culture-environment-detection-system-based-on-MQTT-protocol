# app/routes/data_routes.py

from flask import Blueprint, request, jsonify

from app.models import db, SensorData, Sensor, SensorType

data_bp = Blueprint('data_bp', __name__)


@data_bp.route('/api/data', methods=['GET'])
def get_sensor_data():
    sensor_id = request.args.get('sensor_id')
    type_id = request.args.get('type_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    query = SensorData.query.filter_by(is_deleted=False)

    if sensor_id:
        query = query.filter_by(sensor_id=sensor_id)

    if type_id:
        query = query.filter_by(type_id=type_id)

    if start_time:
        query = query.filter(SensorData.timestamp >= start_time)

    if end_time:
        query = query.filter(SensorData.timestamp <= end_time)

    data_records = query.all()
    data_list = [{
        'data_id': record.data_id,
        'sensor_id': record.sensor_id,
        'type_id': record.type_id,
        'timestamp': record.timestamp,
        'value': record.value,
        'created_at': record.created_at
    } for record in data_records]

    return jsonify(data_list), 200


@data_bp.route('/api/data', methods=['POST'])
def insert_sensor_data():
    data = request.json

    sensor_id = data.get('sensor_id')
    type_id = data.get('type_id')
    timestamp = data.get('timestamp')
    value = data.get('value')

    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404

    sensor_type = SensorType.query.get(type_id)
    if sensor_type is None:
        return jsonify({'error': 'Sensor type not found'}), 404

    new_data = SensorData(
        sensor_id=sensor_id,
        type_id=type_id,
        timestamp=timestamp,
        value=value
    )

    db.session.add(new_data)
    db.session.commit()

    return jsonify({'message': 'Data inserted', 'data_id': new_data.data_id}), 201


@data_bp.route('/api/data/<data_id>', methods=['DELETE'])
def delete_sensor_data(data_id):
    data_record = SensorData.query.get(data_id)
    if data_record is None or data_record.is_deleted:
        return jsonify({'error': 'Data not found'}), 404

    data_record.is_deleted = True
    db.session.commit()

    return jsonify({'message': 'Data marked as deleted'}), 200

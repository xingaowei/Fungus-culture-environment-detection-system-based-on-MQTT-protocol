# app/routes/sensor_board_routes.py

import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import db, Sensor, SensorMetadata, SensorData, SensorType, SensorStatusHistory

sensor_board_bp = Blueprint('sensor_board_bp', __name__)


@sensor_board_bp.route('/api/sensor_board/sensors', methods=['GET'])
def get_active_sensors():
    sensors = Sensor.query.filter_by(status='active').all()
    sensors_list = [{
        'sensor_id': sensor.sensor_id,
        'name': sensor.name,
        'location': sensor.location,
        'updated_at': sensor.updated_at,
        'data': {
            'temperature': 23.5,
            'humidity': 55.0,
            'co2': 400.0
        },
        'status': sensor.status
    } for sensor in sensors]
    return jsonify(sensors_list), 200


@sensor_board_bp.route('/api/sensor_board/<sensor_id>/thresholds', methods=['GET'])
def get_sensor_thresholds(sensor_id):
    metadata = SensorMetadata.query.filter_by(sensor_id=sensor_id, meta_key='thresholds', is_deleted=False).first()

    if not metadata:
        return jsonify({'error': 'Thresholds not found for the given sensor'}), 404

    try:
        thresholds = json.loads(metadata.meta_value)
    except json.JSONDecodeError:
        try:
            thresholds = eval(metadata.meta_value)
        except Exception as e:
            return jsonify(
                {'error': f'Failed to parse thresholds metadata. {str(e)}', 'raw_value': metadata.meta_value}), 500

    return jsonify({'sensor_id': sensor_id, 'thresholds': thresholds}), 200


@sensor_board_bp.route('/api/sensor_board/<sensor_id>/thresholds', methods=['PUT'])
def update_sensor_thresholds(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if not sensor:
        return jsonify({'error': 'Sensor not found'}), 404

    if not request.is_json or 'thresholds' not in request.json:
        return jsonify({'error': "'thresholds' key is required in the JSON body"}), 400

    new_thresholds = request.json['thresholds']
    if not isinstance(new_thresholds, dict):
        return jsonify({'error': 'Invalid thresholds format. Expected a JSON object (dictionary).'}), 400

    try:
        new_meta_value = json.dumps(new_thresholds)
    except (TypeError, ValueError) as e:
        return jsonify({'error': f'Failed to serialize thresholds. {str(e)}'}), 500

    metadata = SensorMetadata.query.filter_by(sensor_id=sensor_id, meta_key='thresholds', is_deleted=False).first()

    if metadata:
        metadata.meta_value = new_meta_value
    else:
        metadata = SensorMetadata(sensor_id=sensor_id, meta_key='thresholds', meta_value=new_meta_value)
        db.session.add(metadata)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update thresholds metadata. {str(e)}'}), 500

    return jsonify(
        {'message': 'Thresholds updated successfully', 'sensor_id': sensor_id, 'thresholds': new_thresholds}), 200


@sensor_board_bp.route('/api/sensor_board/<sensor_id>/history', methods=['GET'])
def get_historical_data(sensor_id):
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    try:
        start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return jsonify({'error': 'Invalid time format, should be YYYY-MM-DDTHH:MM:SS.sssZ'}), 400

    type_ids = {
        'temperature': get_type_id_by_name('Temperature'),
        'humidity': get_type_id_by_name('Humidity'),
        'co2': get_type_id_by_name('CO2 Concentration')
    }

    sensor_data_records = db.session.query(SensorData.timestamp, SensorData.value, SensorData.type_id).filter(
        SensorData.sensor_id == sensor_id,
        SensorData.timestamp >= start_time,
        SensorData.timestamp <= end_time,
        SensorData.is_deleted == 0
    ).all()

    data_dict = {
        'temperature': [],
        'humidity': [],
        'co2': []
    }

    for record in sensor_data_records:
        if record.type_id == type_ids['temperature']:
            data_dict['temperature'].append(
                {'timestamp': record.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z', 'value': record.value})
        elif record.type_id == type_ids['humidity']:
            data_dict['humidity'].append(
                {'timestamp': record.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z', 'value': record.value})
        elif record.type_id == type_ids['co2']:
            data_dict['co2'].append(
                {'timestamp': record.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z', 'value': record.value})

    return jsonify(data_dict), 200


def get_type_id_by_name(type_name):
    sensor_type = SensorType.query.filter_by(type_name=type_name).first()
    return sensor_type.type_id if sensor_type else None


@sensor_board_bp.route('/api/sensor_board/<sensor_id>/status', methods=['GET'])
def get_sensors_status(sensor_id):
    try:
        latest_status = (
            db.session.query(SensorStatusHistory.status)
            .filter(SensorStatusHistory.sensor_id == sensor_id)
            .order_by(SensorStatusHistory.timestamp.desc())
            .limit(1)
            .subquery()
        )

        sensor_status = db.session.query(latest_status.c.status).first()

        if sensor_status:
            return jsonify({'status': sensor_status[0]})
        else:
            return jsonify({'error': 'Sensor not found or no status history exists'}), 404

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# app/routes/status_routes.py

from flask import Blueprint, request, jsonify

from app.models import db, SensorStatusHistory, Sensor

status_bp = Blueprint('status_bp', __name__)


@status_bp.route('/api/sensors/<sensor_id>/status', methods=['PUT'])
def update_sensor_status(sensor_id):
    if Sensor.query.filter_by(sensor_id=sensor_id).first() is None:
        return jsonify({'error': 'Sensor does not exist'}), 404
    data = request.json
    new_status = data.get('status')

    if new_status not in ['normal', 'warning', 'offline', 'disabled']:
        return jsonify({'error': 'Invalid status value'}), 400

    status_history = SensorStatusHistory(
        sensor_id=sensor_id,
        status=new_status,
        timestamp=db.func.current_timestamp()
    )
    db.session.add(status_history)
    db.session.commit()

    return jsonify(status_history.to_dict()), 200


@status_bp.route('/api/sensors/<sensor_id>/status', methods=['GET'])
def get_sensor_status_history(sensor_id):
    status_history = SensorStatusHistory.query.filter_by(sensor_id=sensor_id).all()
    history_list = [{
        'status_id': record.status_id,
        'status': record.status,
        'timestamp': record.timestamp,
        'created_at': record.created_at
    } for record in status_history]

    if len(history_list) == 0:
        return jsonify({'error': 'No status history recorded.'}), 404

    return jsonify(history_list), 200


@status_bp.route('/api/sensors/<sensor_id>/latest_status', methods=['GET'])
def get_latest_sensor_status(sensor_id):
    sensor = Sensor.query.get(sensor_id)
    if not sensor:
        return jsonify({'error': 'Sensor not found'}), 404

    latest_status = db.session.query(SensorStatusHistory).filter_by(sensor_id=sensor_id).order_by(
        SensorStatusHistory.timestamp.desc()).first()

    if latest_status:
        return jsonify({
            'sensor_id': sensor_id,
            'status': latest_status.status,
            'timestamp': latest_status.timestamp
        }), 200
    else:
        return jsonify({'error': 'No status history found for this sensor'}), 404

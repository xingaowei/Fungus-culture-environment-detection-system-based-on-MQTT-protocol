# app/routes/alerts_routes.py

import uuid

from flask import Blueprint, request, jsonify

from app.models import db, Alert, Sensor

alerts_bp = Blueprint('alerts_bp', __name__)


@alerts_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = Alert.query.all()
    return jsonify([alert.to_dict() for alert in alerts])


@alerts_bp.route('/api/alerts', methods=['POST'])
def create_alert():
    data = request.json

    sensor_id = data.get('sensor_id')
    alert_type = data.get('alert_type')
    message = data.get('message')

    if not sensor_id or not alert_type or not message:
        return jsonify({'error': 'Missing required fields'}), 400

    sensor = Sensor.query.get(sensor_id)
    if sensor is None:
        return jsonify({'error': 'Sensor not found'}), 404

    new_alert = Alert(
        alert_id=str(uuid.uuid4()),
        sensor_id=sensor_id,
        alert_type=alert_type,
        message=message
    )

    db.session.add(new_alert)
    db.session.commit()

    return jsonify({'message': 'Alert created', 'alert_id': new_alert.alert_id}), 201


@alerts_bp.route('/api/alerts/<alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    alert = Alert.query.get(alert_id)
    if alert is None:
        return jsonify({'error': 'Alert not found'}), 404

    alert.is_deleted = True
    db.session.commit()

    return jsonify({'message': 'Alert marked as deleted'}), 200


@alerts_bp.route('/api/alerts/<alert_id>/acknowledge', methods=['PUT'])
def mark_alert_acknowledged(alert_id):
    alert = Alert.query.get(alert_id)
    if alert is None or alert.is_deleted:
        return jsonify({'error': 'Alert not found'}), 404

    if alert.status == 'resolved':
        return jsonify({'message': 'Alert been resolved'}), 409

    alert.status = 'acknowledged'
    db.session.commit()

    return jsonify({'message': 'Alert marked as acknowledged'}), 200


@alerts_bp.route('/api/alerts/<alert_id>/resolve', methods=['PUT'])
def mark_alert_resolved(alert_id):
    alert = Alert.query.get(alert_id)
    if alert is None or alert.is_deleted:
        return jsonify({'error': 'Alert not found'}), 404

    alert.status = 'resolved'
    db.session.commit()

    return jsonify({'message': 'Alert marked as resolved'}), 200


@alerts_bp.route('/api/alerts/clear', methods=['DELETE'])
def clear_all_alerts():
    alerts = Alert.query.filter_by(is_deleted=False).all()

    for alert in alerts:
        alert.is_deleted = True

    db.session.commit()

    return jsonify({'message': 'All alerts cleared'}), 200

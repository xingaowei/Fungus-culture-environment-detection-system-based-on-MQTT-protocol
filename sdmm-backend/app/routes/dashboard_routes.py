# app/routes/dashboard_routes.py

from flask import Blueprint, jsonify
from sqlalchemy import func

from app.models import db, SensorStatusHistory

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/api/dashboard/sensor-status-summary', methods=['GET'])
def get_sensor_status_summary():
    subquery = db.session.query(
        SensorStatusHistory.sensor_id,
        func.max(SensorStatusHistory.timestamp).label('latest_timestamp'),
        func.max(SensorStatusHistory.status_id).label('latest_status_id')
    ).group_by(SensorStatusHistory.sensor_id).subquery()

    latest_status_query = db.session.query(
        SensorStatusHistory.status,
        func.count(SensorStatusHistory.sensor_id).label('count')
    ).join(
        subquery,
        (SensorStatusHistory.sensor_id == subquery.c.sensor_id) &
        (SensorStatusHistory.timestamp == subquery.c.latest_timestamp) &
        (SensorStatusHistory.status_id == subquery.c.latest_status_id)
    ).group_by(SensorStatusHistory.status).all()

    status_summary = {
        'normal': 0,
        'warning': 0,
        'offline': 0,
        'disabled': 0
    }

    for status, count in latest_status_query:
        if status in status_summary:
            status_summary[status] = count

    return jsonify(status_summary), 200

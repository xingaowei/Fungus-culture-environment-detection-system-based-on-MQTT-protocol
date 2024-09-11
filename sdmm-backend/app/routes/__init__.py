# app/routes/__init__.py

from app.routes.alerts_routes import alerts_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.data_routes import data_bp
from app.routes.mapping_routes import mapping_bp
from app.routes.metadata_routes import metadata_bp
from app.routes.sensor_board_routes import sensor_board_bp
from app.routes.sensor_routes import sensor_bp
from app.routes.status_routes import status_bp
from app.routes.subscription_routes import subscription_bp
from app.routes.type_rotues import type_bp


def register_routes(app):
    app.register_blueprint(sensor_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(mapping_bp)
    app.register_blueprint(metadata_bp)
    app.register_blueprint(type_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sensor_board_bp)
    app.register_blueprint(alerts_bp)

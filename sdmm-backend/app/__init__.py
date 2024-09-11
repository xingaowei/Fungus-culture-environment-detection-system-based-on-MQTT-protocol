# app/__init__.py

from flask import Flask

from app.models import db
from app.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    db.init_app(app)
    register_routes(app)

    return app

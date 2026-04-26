"""
NexusQuery — Databricks AI Chat Application
Flask application factory.
"""
from flask import Flask
from .routes.chat import chat_bp
from .routes.home import home_bp
from .routes.health import health_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(health_bp, url_prefix="/health")

    return app

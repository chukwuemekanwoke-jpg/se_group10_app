"""
Flask Application Factory.
Creates and configures the app instance.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from app.config import config
from app.database import db, init_db
from app.services import AuthService, BikeService

load_dotenv()

def init_db(app):
    """Initialize the database with the app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    #Read environment name from .env - default to "development" if not set

    config_name = os.getenv("FLASK_ENV", "development")

    config_class = config.get(config_name)
    if not config_class:
        raise RuntimeError(
            f"Unknown FLASK_ENV value: '{config_name}'. "
            f"Expected one of: {list(config.keys())}"
        )

    app.config.from_object(config_class)

    #Logging
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    #Database
    init_db(app)

    #CORS
    CORS(app)
    
    # Register blueprints
    from app.main import main_bp
    from app.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    register_error_handlers(app)

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Resource not found"), 404
        return "Page not found", 404

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Access denied"), 403
        return "Access denied", 403

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Internal server error"), 500
        return "Internal server error", 500

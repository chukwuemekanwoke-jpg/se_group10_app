"""
Flask Application Factory.
Creates and configures the app instance.
"""

import os
import logging # standard-library module — must NOT be shadowed
import logging.handlers
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from dotenv import load_dotenv
from app.config import config
from app.database import db, init_db

load_dotenv()

cache = Cache(app, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'CACHE_DEFAULT_TIMEOUT': 600
    })

def create_app():


    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # Read environment name from .env - default to "development" if not set
    config_name = os.getenv("FLASK_ENV", "development")

    config_class = config.get(config_name)
    if not config_class:
        raise RuntimeError(
            f"Unknown FLASK_ENV value: '{config_name}'. "
            f"Expected one of: {list(config.keys())}"
        )

    app.config.from_object(config_class)

    if not app.config.get("TESTING"):
        host     = os.getenv("DB_HOST", "localhost")
        user     = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        name     = os.getenv("DB_NAME", "dublin_bikes")
        port     = int(os.getenv("DB_PORT", 3306))
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        )

    # Logging configuration
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # File logging for production
    if not app.debug and not app.testing:
        
        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = logging.handlers.RotatingFileHandler(
            "logs/troithean.log",
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)

    # Database initialization
    init_db(app)

    # CORS
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

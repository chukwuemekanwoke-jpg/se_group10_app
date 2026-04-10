"""
Flask Application Factory.
Creates and configures the app instance.
"""

import os
import logging # standard-library module — must NOT be shadowed
import logging.handlers
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from dotenv import load_dotenv
from app.config import config
from app.database import db, init_db

load_dotenv()

# Initialize cache as None - will be set in create_app()
cache = None

def create_app():
    """
    Application factory function.
    Creates and configures a Flask app instance.
    
    Returns:
        Flask: Configured Flask application
    """
    global cache
    
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

    # Configure database URI if not testing
    if not app.config.get("TESTING"):
        host     = os.getenv("DB_HOST", "localhost")
        user     = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        name     = os.getenv("DB_NAME", "dublin_bikes")
        port     = int(os.getenv("DB_PORT", 3306))
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        )

    # Initialize cache AFTER app is created
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    cache = Cache(app, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': redis_url,
        'CACHE_DEFAULT_TIMEOUT': 600
    })

    # Logging configuration
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # File logging for production
    if not app.debug and not app.testing:
        # Create logs directory with absolute path
        log_dir = Path(app.instance_path) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "troithean.log"

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_file),
            maxBytes=10_240_000,  # 10MB
            backupCount=5         # Reduced from 10 for t3.micro disk space
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

    # Cleanup database connection on request end
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    register_error_handlers(app)
    
    # Initialize middleware
    from app.middleware import init_middleware
    init_middleware(app)

    return app


def register_error_handlers(app):
    """Register Flask error handlers for API and web routes."""
    
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
        app.logger.error(f"Internal server error: {error}")
        if request.path.startswith("/api/"):
            return jsonify(error="Internal server error"), 500
        return "Internal server error", 500

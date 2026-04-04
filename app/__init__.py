import os
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("Missing required environment variable: SECRET_KEY")

    app.config["SECRET_KEY"] = secret_key
    app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")
    app.config["JCDECAUX_API_KEY"] = os.getenv("JCDECAUX_API_KEY")
    app.config["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY")

    logging.basicConfig(level=logging.INFO)

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

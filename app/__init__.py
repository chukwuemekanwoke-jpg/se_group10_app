from flask import Flask
from dotenv import load_dotenv
from .main import main_bp
from .api import api_bp
import os

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("Missing required environment variable: SECRET_KEY")

    app.config["SECRET_KEY"] = secret_key
    app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")
    app.config["JCDECAUX_API_KEY"] = os.getenv("JCDECAUX_API_KEY")
    app.config["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY")

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

from flask import Flask
from dotenv import load_dotenv
from .db import close_db
from app.main import main_bp
from app.api import api_bp
import os

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

    app.teardown_appcontext(close_db)

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    
    app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY", "")

    return app

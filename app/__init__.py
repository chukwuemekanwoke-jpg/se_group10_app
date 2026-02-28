from flask import Flask
from dotenv import load_dotenv
from db import close_db

def create_app():
    load_dotenv()

    app = Flask(__name__)

    # Close DB connections after request
    app.teardown_appcontext(close_db)

    # Register Blueprints
    from app.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.api import api_bp
    app.register_blueprint(api_bp)

    return app

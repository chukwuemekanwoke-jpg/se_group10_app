"""
app.py - Main Flask Application File
Dublin Bikes Web App - COMP30830 Project - Troithean

This is the main entry point for the Flask app.
It combines routes for: serving pages, DB data, live API data, and ML predictions.
"""

import os
import logging
from flask import Flask, g, jsonify, render_template, request, abort, session
from sqlalchemy import create_engine
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------------
# App Setup
# static_url_path='' means static files are served from /static folder
# -------------------------------------------------------
app = Flask(__name__, static_url_path='')

# Secret key for sessions - loaded from .env
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Logging setup
logging.basicConfig(level=logging.INFO)


# -------------------------------------------------------
# Database Configuration
# All values loaded from .env file - never hardcoded
# -------------------------------------------------------
DB_USER     = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT     = os.getenv('DB_PORT', '3306')
DB_NAME     = os.getenv('DB_NAME')
DB_HOST     = os.getenv('DB_HOST', '127.0.0.1')

def connect_to_db():
    connection_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(
        DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
    )
    engine = create_engine(connection_string, echo=True)
    return engine

def get_db():
    """Store DB engine in Flask's global 'g' so it's reused per request."""
    db_engine = getattr(g, '_database', None)
    if db_engine is None:
        db_engine = g._database = connect_to_db()
    return db_engine


# -------------------------------------------------------
# Live API Configuration
# All keys loaded from .env file - never hardcoded
# -------------------------------------------------------
JCDECAUX_API_KEY    = os.getenv('JCDECAUX_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
CITY_NAME           = "Dublin"
CONTRACT_NAME       = "dublin"

def get_bike_data():
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract={CONTRACT_NAME}&apiKey={JCDECAUX_API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}


# -------------------------------------------------------
# Page Routes
# -------------------------------------------------------

@app.route('/')
def root():
    """Serve the main index page."""
    return app.send_static_file('index.html')


# -------------------------------------------------------
# API Routes - DB Data
# -------------------------------------------------------

@app.route('/api/stations')
def get_stations():
    """Return all stations from the database as JSON."""
    engine = get_db()
    stations = []
    rows = engine.execute("SELECT * FROM station;")
    for row in rows:
        stations.append(dict(row))
    return jsonify(stations=stations)

@app.route('/api/availability/<int:station_id>')
def get_availability(station_id):
    """Return available bikes for a specific station."""
    engine = get_db()
    data = []
    rows = engine.execute(
        "SELECT available_bikes FROM availability WHERE number = {};".format(station_id)
    )
    for row in rows:
        data.append(dict(row))

    if not data:
        abort(404)

    return jsonify(available=data)


# -------------------------------------------------------
# API Routes - Live Data
# -------------------------------------------------------

@app.route('/api/bikes/live')
def live_bikes():
    """Return live JCDecaux bike station data."""
    return jsonify(get_bike_data())

@app.route('/api/weather')
def live_weather():
    """Return current weather from OpenWeatherMap."""
    return jsonify(get_weather())


# -------------------------------------------------------
# ML Prediction Route (placeholder - add your model here)
# -------------------------------------------------------

@app.route('/api/predict/<int:station_id>')
def predict(station_id):
    """Return bike availability prediction for a station."""
    # TODO: Load your trained ML model and return a prediction
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model not connected yet"
    })


# -------------------------------------------------------
# Error Handlers
# -------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Resource not found"), 404

@app.errorhandler(403)
def forbidden(e):
    return jsonify(error="Access denied"), 403


# -------------------------------------------------------
# Run the App
# host="0.0.0.0" is REQUIRED for EC2 deployment
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

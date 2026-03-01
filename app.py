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
import requests

# -------------------------------------------------------
# App Setup (from 1__basic2.py)
# static_url_path='' means static files are served from /static folder
# -------------------------------------------------------
app = Flask(__name__, static_url_path='')

# Secret key for sessions (from 13__secret_key.py)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'd5ac188faa9eb221139d1e3b07f69a21978a2c94f3520161bf8d3f4872852a4e')

# Logging setup
logging.basicConfig(filename='app.log', level=logging.INFO)


# -------------------------------------------------------
# Database Configuration (from 8__flask-connection-to-db.py & 9__connection_complex.py)
# -------------------------------------------------------
DB_USER     = "root"
DB_PASSWORD = "MbArsenal44"       # TODO: replaced--
DB_PORT     = "3306"
DB_NAME     = "dublinbikes-db"  # TODO: replaced--
DB_HOST     = "127.0.0.1"

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
# Live API Configuration (from 9_1_get_currrent_data.py)
# -------------------------------------------------------
JCDECAUX_API_KEY      = os.getenv('JCDECAUX_API_KEY', '9ba379feaef0ee113d0fffac70c29a1804bcde56')   # TODO: replaced--
OPENWEATHER_API_KEY   = os.getenv('OPENWEATHER_API_KEY', '1444bd9e66875a953d0b2409c58241a1') # TODO: replaced--
CITY_NAME             = "Dublin"
CONTRACT_NAME         = "dublin"

def get_bike_data():
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract={CONTRACT_NAME}&apiKey={JCDECAUX_API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}


# -------------------------------------------------------
# Page Routes (from 1__basic2.py, 2__basic2.py, 3__basic3.py)
# -------------------------------------------------------

@app.route('/')
def root():
    """Serve the main index page."""
    return app.send_static_file('index.html')


# -------------------------------------------------------
# API Routes - DB Data (from 8__flask-connection-to-db.py & 9__connection_complex.py)
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
        abort(404)  # from 14__abort.py - station not found

    return jsonify(available=data)


# -------------------------------------------------------
# API Routes - Live Data (from 9_1_get_currrent_data.py)
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
    """Return bike availability prediction for a station. Placeholder for ML model."""
    # TODO: Load your trained ML model and return a prediction
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model not connected yet"
    })


# -------------------------------------------------------
# Error Handlers (from 14__abort.py)
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

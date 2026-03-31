"""
app.py - Main Flask Application File
Dublin Bikes Web App - COMP30830 Project - Troithean

This is the main entry point for the Flask app.
It combines routes for: serving pages, DB data, live API data, and ML predictions.
"""

import os
import logging
import requests
from flask import Flask, jsonify, request, abort, session, redirect, url_for
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env on EC2
load_dotenv()

# -------------------------------------------------------
# App Setup
# -------------------------------------------------------
app = Flask(__name__, static_url_path='')

# Securely load from .env - critical for production sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Logging setup for monitoring production traffic/errors
logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------
# RDS Database Configuration (Optimized for AWS)
# -------------------------------------------------------
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT     = os.getenv('DB_PORT', '3306')
DB_NAME     = os.getenv('DB_NAME')
DB_HOST     = os.getenv('DB_HOST')

# Connection pooling ensures the EC2 doesn't overwhelm the RDS instance
connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(
    connection_string,
    pool_size=10,        # Number of permanent connections to RDS
    max_overflow=20,     # Temporary extra connections for high traffic
    pool_recycle=3600    # Prevent "MySQL Server has gone away" errors
)

# -------------------------------------------------------
# [SECTION] User Authentication & Login (Placeholders)
# -------------------------------------------------------

@app.route('/api/register', methods=['POST'])
def register():
    """Placeholder for user registration logic."""
    # TODO: Hash password and save to RDS 'users' table
    return jsonify({"message": "Registration logic placeholder"})

@app.route('/api/login', methods=['POST'])
def login():
    """Placeholder for session-based login logic."""
    # TODO: Verify credentials and set session['user_id']
    return jsonify({"message": "Login logic placeholder"})

@app.route('/api/logout')
def logout():
    """Placeholder for session clearing."""
    session.pop('user_id', None)
    return redirect(url_for('root'))


# -------------------------------------------------------
# [SECTION] ML Prediction Logic (Placeholder)
# -------------------------------------------------------

@app.route('/api/predict/<int:station_id>')
def predict(station_id):
    """Placeholder for ML model inference."""
    # TODO: Load .pkl model and predict based on time/weather
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model logic placeholder"
    })


# -------------------------------------------------------
# Live External API Data (JCDecaux & Weather)
# -------------------------------------------------------
JCDECAUX_API_KEY    = os.getenv('JCDECAUX_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def get_bike_data():
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={JCDECAUX_API_KEY}"
    try:
        # Timeout prevents your whole site from hanging if the API is slow
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        logging.error(f"JCDecaux API Error: {e}")
        return []

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        logging.error(f"Weather API Error: {e}")
        return []


# -------------------------------------------------------
# RDS API Routes (Optimized for Performance & Security)
# -------------------------------------------------------

@app.route('/')
def root():
    """Serve the frontend index file."""
    return app.send_static_file('index.html')

@app.route('/api/stations')
def get_stations():
    stations = []
    try:
        with engine.connect() as connection:
            # text() and _mapping provide compatibility with SQLAlchemy 2.0+
            result = connection.execute(text("SELECT * FROM station;"))
            for row in result:
                stations.append(dict(row._mapping))
        return jsonify(stations=stations)
    except Exception as e:
        logging.error(f"RDS Fetch Error: {e}")
        abort(500)

@app.route('/api/availability/<int:station_id>')
def get_availability(station_id):
    data = []
    try:
        with engine.connect() as connection:
            # Parameterized query protects your RDS from SQL injection attacks
            query = text("SELECT available_bikes, last_update FROM availability WHERE number = :id ORDER BY last_update DESC LIMIT 100")
            result = connection.execute(query, {"id": station_id})
            for row in result:
                data.append(dict(row._mapping))
        
        if not data:
            abort(404)
        return jsonify(available=data)
    except Exception as e:
        logging.error(f"RDS Query Error: {e}")
        abort(500)

@app.route('/api/bikes/live')
def live_bikes():
    return jsonify(get_bike_data())

@app.route('/api/weather')
def live_weather():
    return jsonify(get_weather())


# -------------------------------------------------------
# Error Handlers
# Prevents leaking system info to users during failures.
# -------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Resource not found"), 404

@app.errorhandler(403)
def forbidden(e):
    return jsonify(error="Access denied"), 403

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error="Internal server error"), 500


# -------------------------------------------------------
# Run App
# -------------------------------------------------------
if __name__ == "__main__":
    # host="0.0.0.0" is mandatory for AWS EC2 to be reachable.
    # Set debug=False when you are finished testing.
    app.run(debug=True, host="0.0.0.0", port=5000)
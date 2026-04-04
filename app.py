"""
app.py - Main Flask Application File
Dublin Bikes Web App - COMP30830 Project - Troithean

Main entry point for the Flask app.
Handles:
- Template rendering
- RDS database routes
- Live external API data
- Placeholder authentication
- Placeholder ML prediction
"""

import os
import logging
import requests
from flask import (
    Flask,
    jsonify,
    request,
    abort,
    session,
    redirect,
    url_for,
    render_template
)
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# -------------------------------------------------------
# App Setup
# -------------------------------------------------------
app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Logging setup
logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------
# RDS Database Configuration
# -------------------------------------------------------
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')

connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    connection_string,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# -------------------------------------------------------
# External API Keys
# -------------------------------------------------------
JCDECAUX_API_KEY = os.getenv('JCDECAUX_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# -------------------------------------------------------
# Helper Functions
# -------------------------------------------------------
def get_bike_data():
    """Fetch live Dublin Bikes station data from JCDecaux API."""
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={JCDECAUX_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        logging.error(f"JCDecaux API Error: {e}")
        return []

def get_weather():
    """Fetch current Dublin weather from OpenWeather API."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        logging.error(f"Weather API Error: {e}")
        return {}

# -------------------------------------------------------
# Frontend Page Routes
# -------------------------------------------------------
@app.route('/')
def root():
    """Render the main homepage/map page."""
    return render_template(
        'index.html',
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

@app.route('/login')
def login_page():
    """Render the login page."""
    return render_template('login.html')

# -------------------------------------------------------
# User Authentication Routes (Placeholders)
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
    """Clear the current user session."""
    session.pop('user_id', None)
    return redirect(url_for('root'))

# -------------------------------------------------------
# ML Prediction Route (Placeholder)
# -------------------------------------------------------
@app.route('/api/predict/<int:station_id>')
def predict(station_id):
    """Placeholder for ML model inference."""
    # TODO: Load model.pkl and predict based on time/weather
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model logic placeholder"
    })

# -------------------------------------------------------
# RDS API Routes
# -------------------------------------------------------
@app.route('/api/stations')
def get_stations():
    """Fetch all station records from the database."""
    stations = []
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM station;"))
            for row in result:
                stations.append(dict(row._mapping))
        return jsonify(stations=stations)
    except Exception as e:
        logging.error(f"RDS Fetch Error: {e}")
        abort(500)

@app.route('/api/availability/<int:station_id>')
def get_availability(station_id):
    """Fetch recent availability history for a station."""
    data = []
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT available_bikes, last_update
                FROM availability
                WHERE number = :id
                ORDER BY last_update DESC
                LIMIT 100
            """)
            result = connection.execute(query, {"id": station_id})

            for row in result:
                data.append(dict(row._mapping))

        if not data:
            abort(404)

        return jsonify(available=data)
    except Exception as e:
        logging.error(f"RDS Query Error: {e}")
        abort(500)

# -------------------------------------------------------
# Live External API Routes
# -------------------------------------------------------
@app.route('/api/bikes/live')
def live_bikes():
    """Return live bike station data from JCDecaux."""
    return jsonify(get_bike_data())

@app.route('/api/weather')
def live_weather():
    """Return live weather data from OpenWeather."""
    return jsonify(get_weather())

# -------------------------------------------------------
# Error Handlers
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
    # Use debug=False in production
    app.run(debug=True, host="0.0.0.0", port=5000)

import logging
import requests
from flask import jsonify, abort, current_app
from werkzeug.exceptions import HTTPException
from . import api_bp
from app.db import get_db

logger = logging.getLogger(__name__)


def get_bike_data():
    api_key = current_app.config.get("JCDECAUX_API_KEY")
    if not api_key:
        logger.warning("JCDECAUX_API_KEY not set")
        return []

    url = f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("JCDecaux API Error: %s", e)
        return []


def get_weather():
    api_key = current_app.config.get("OPENWEATHER_API_KEY")
    if not api_key:
        logger.warning("OPENWEATHER_API_KEY not set")
        return {}

    url = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Weather API Error: %s", e)
        return {}


@api_bp.route("/stations")
def get_stations():
    stations = []
    db = None
    cur = None

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM station")
        stations = cur.fetchall()

        return jsonify(stations=stations)

    except Exception as e:
        logger.error("RDS Fetch Error: %s", e)
        abort(500)

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


@api_bp.route("/availability/<int:station_id>")
def get_availability(station_id):
    db = None
    cur = None

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            SELECT available_bikes, last_update
            FROM availability
            WHERE number = %s
            ORDER BY last_update DESC
            LIMIT 100
        """, (station_id,))
        data = cur.fetchall()

        if not data:
            abort(404)

        return jsonify(available=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("RDS Query Error: %s", e)
        abort(500)

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


@api_bp.route("/bikes/live")
def live_bikes():
    return jsonify(get_bike_data())


@api_bp.route("/weather")
def live_weather():
    return jsonify(get_weather())


@api_bp.route("/predict/<int:station_id>")
def predict(station_id):
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model logic placeholder"
    })


@api_bp.route("/register", methods=["POST"])
def register_api():
    return jsonify({"message": "Registration logic placeholder"})


@api_bp.route("/login", methods=["POST"])
def login_api():
    return jsonify({"message": "Login API placeholder"})

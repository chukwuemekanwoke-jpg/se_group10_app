import os
import requests
from flask import jsonify, request, abort
from . import api_bp
from app.db import get_db
import joblib
import pandas as pd
from datetime import datetime

@api_bp.route("/stations")
def api_stations():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            number,
            name,
            address,
            position_lat,
            position_lng,
            bike_stands,
            status
        FROM station;
    """)

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)


@api_bp.route("/latest")
def api_latest():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT a.number, a.last_update, a.available_bikes, a.available_bike_stands, a.status
        FROM availability a
        JOIN (
            SELECT number, MAX(last_update) AS max_time
            FROM availability
            GROUP BY number
        ) t
          ON a.number = t.number AND a.last_update = t.max_time
        ORDER BY a.number;
    """)

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)


@api_bp.route("/availability")
def api_availability():
    number = request.args.get("number", type=int)
    limit = request.args.get("limit", default=50, type=int)

    if number is None:
        abort(400, description="Missing number")

    limit = max(1, min(limit, 500))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT number, last_update, available_bikes, available_bike_stands, status
        FROM availability
        WHERE number = %s
        ORDER BY last_update DESC
        LIMIT %s;
    """, (number, limit))

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)


@api_bp.route("/weather/latest")
def api_weather_latest():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM weather_current
        ORDER BY dt_unix DESC
        LIMIT 1;
    """)

    row = cur.fetchone()
    cur.close()
    return jsonify(row or {})


@api_bp.route("/weather")
def api_weather():
    limit = request.args.get("limit", default=48, type=int)
    limit = max(1, min(limit, 500))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM weather_current
        ORDER BY dt_unix DESC
        LIMIT %s;
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)


@api_bp.route("/live/bikes")
def api_live_bikes():
    api_key = os.getenv("JCDECAUX_API_KEY")
    contract = os.getenv("JCDECAUX_CONTRACT_NAME", "Dublin")

    if not api_key:
        return jsonify({"error": "Missing JCDECAUX_API_KEY"}), 500

    url = "https://api.jcdecaux.com/vls/v1/stations"
    params = {"contract": contract, "apiKey": api_key}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/live/weather")
def api_live_weather():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    lat = os.getenv("WEATHER_LAT", "53.3498")
    lon = os.getenv("WEATHER_LON", "-6.2603")

    if not api_key:
        return jsonify({"error": "Missing OPENWEATHER_API_KEY"}), 500

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/predict")
def api_predict():
    station_id = request.args.get("station_id", type=int)
    date_str = request.args.get("date")
    time_str = request.args.get("time")

    if station_id is None or not date_str or not time_str:
        return jsonify({"error": "Missing station_id, date, or time"}), 400

    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Get station information
    cur.execute("""
        SELECT number, name, bike_stands, position_lat, position_lng
        FROM station
        WHERE number = %s
    """, (station_id,))
    station = cur.fetchone()

    if not station:
        cur.close()
        return jsonify({"error": "Station not found"}), 404

    # Get latest weather from database for now
    cur.execute("""
        SELECT temp, humidity, pressure
        FROM weather_current
        ORDER BY dt_unix DESC
        LIMIT 1
    """)
    weather = cur.fetchone()
    cur.close()

    if not weather:
        return jsonify({"error": "Weather data unavailable"}), 500

    # Build feature row to match notebook features
    input_df = pd.DataFrame([{
        "station_id": station["number"],
        "capacity": station["bike_stands"],
        "hour": dt.hour,
        "month": dt.month,
        "day_of_week": dt.weekday(),
        "is_weekend": 1 if dt.weekday() in [5, 6] else 0,
        "rush_hour": 1 if dt.hour in [7, 8, 9, 16, 17, 18] else 0,
        "lat": float(station["position_lat"]),
        "lon": float(station["position_lng"]),
        "max_air_temperature_celsius": float(weather["temp"]),
        "max_relative_humidity_percent": float(weather["humidity"]),
        "max_barometric_pressure_hpa": float(weather["pressure"]),
    }])

    try:
        model = joblib.load("ml_model/best_bike_model.pkl")
        prediction = model.predict(input_df)[0]
    except Exception as e:
        return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

    prediction = max(0, int(round(float(prediction))))

    return jsonify({
        "station_id": station["number"],
        "station_name": station["name"],
        "date": date_str,
        "time": time_str,
        "predicted_bikes": prediction
    })
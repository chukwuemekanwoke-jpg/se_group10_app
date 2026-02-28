import os
import requests
from flask import jsonify, request, abort
from . import api_bp
from db import get_db


@api_bp.route("/api/stations")
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


@api_bp.route("/api/latest")
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


@api_bp.route("/api/availability")
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


@api_bp.route("/api/weather/latest")
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


@api_bp.route("/api/weather")
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


@api_bp.route("/api/live/bikes")
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


@api_bp.route("/api/live/weather")
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

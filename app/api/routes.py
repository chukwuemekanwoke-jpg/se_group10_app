"""
app/api/routes.py - API Blueprint Routes
Dublin Bikes Web App - COMP30830 Project - Troithean

RESTful API endpoints for the Dublin Bikes application.

Authentication & Security:
- API endpoints do NOT use CSRF tokens (not applicable to REST/JSON APIs)
- CSRF protection is handled in the main blueprint for form-based routes
- Use Bearer tokens or OAuth for API authentication if adding auth later
- Main blueprint routes use Flask session + CSRF tokens for HTML forms

Endpoints:
- GET /api/health                   — Health check for load balancers
- GET /api/stations                 — List all bike stations (ORM)
- GET /api/stations/<id>            — Get specific station details (ORM)
- GET /api/latest                   — Latest availability for all stations (raw SQL, fast)
- GET /api/availability             — Paginated availability history for a station
- GET /api/availability/<id>        — Current availability for a station (ORM)
- GET /api/weather                  — Weather history (paginated)
- GET /api/weather/latest           — Most recent weather record
- GET /api/live/bikes               — Live data from JCDecaux API
- GET /api/live/weather             — Live data from OpenWeather API
- GET /api/predict                  — Bike availability prediction (ML)
"""

import os
import requests as http_requests
from flask import jsonify, request, abort
from app.api import api_bp
from app.services import BikeService, JCDecauxService, WeatherService, PredictionService
from app.database.db import db
from app.database.models import Availability, WeatherCurrent
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Health Check
# ============================================================================

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for load balancers and monitoring services.

    Returns:
        JSON with status and version
        HTTP 200 if healthy
    """
    return jsonify(
        status="healthy",
        version="1.0.0",
        service="Troithean Dublin Bikes API"
    ), 200


# ============================================================================
# Stations Endpoints
# ============================================================================

@api_bp.route("/stations", methods=["GET"])
def get_all_stations():
    """
    Retrieve all Dublin Bikes stations from the database.

    Returns:
        JSON array of station objects
        Each station includes: id, name, address, lat, lng, capacity, status
    """
    try:
        stations = BikeService.get_all_stations()
        return jsonify(stations), 200
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return jsonify(error="Failed to fetch stations"), 500


@api_bp.route("/stations/<int:station_id>", methods=["GET"])
def get_station(station_id):
    """
    Retrieve details for a specific station.

    Args:
        station_id: The station number/ID

    Returns:
        JSON object with station details
        HTTP 404 if station not found
    """
    try:
        station = BikeService.get_station_by_id(station_id)
        if not station:
            return jsonify(error="Station not found"), 404
        return jsonify(station), 200
    except Exception as e:
        logger.error(f"Error fetching station {station_id}: {e}")
        return jsonify(error="Failed to fetch station"), 500


# ============================================================================
# Availability Endpoints
# ============================================================================

@api_bp.route("/latest", methods=["GET"])
def api_latest():
    """
    Latest availability snapshot for every station.
    Uses an optimised subquery for fast response — used by the map frontend.

    Returns:
        JSON array: [{number, last_update, available_bikes, available_bike_stands, status}, ...]
    """
    try:
        result = db.session.execute(db.text("""
            SELECT a.number, a.last_update, a.available_bikes, a.available_bike_stands, a.status
            FROM availability a
            JOIN (
                SELECT number, MAX(last_update) AS max_time
                FROM availability
                GROUP BY number
            ) t ON a.number = t.number AND a.last_update = t.max_time
            ORDER BY a.number
        """))
        rows = [dict(row._mapping) for row in result]
        # Serialise datetime to string for JSON
        for row in rows:
            if row.get("last_update") and hasattr(row["last_update"], "isoformat"):
                row["last_update"] = row["last_update"].isoformat()
        return jsonify(rows), 200
    except Exception as e:
        logger.error(f"Error fetching latest availability: {e}")
        return jsonify(error="Failed to fetch latest availability"), 500


@api_bp.route("/availability", methods=["GET"])
def api_availability():
    """
    Paginated availability history for a specific station.

    Query params:
        number (int, required): Station number
        limit  (int, optional): Max records to return, 1–500, default 50

    Returns:
        JSON array of availability records
        HTTP 400 if station number is missing
    """
    number = request.args.get("number", type=int)
    limit  = request.args.get("limit", default=50, type=int)

    if number is None:
        abort(400, description="Missing required query parameter: number")

    limit = max(1, min(limit, 500))

    try:
        records = (
            db.session.query(Availability)
            .filter_by(number=number)
            .order_by(Availability.last_update.desc())
            .limit(limit)
            .all()
        )
        return jsonify([r.to_dict() for r in records]), 200
    except Exception as e:
        logger.error(f"Error fetching availability for station {number}: {e}")
        return jsonify(error="Failed to fetch availability"), 500


@api_bp.route("/availability/<int:station_id>", methods=["GET"])
def get_station_availability(station_id):
    """
    Get the most recent availability record for a specific station (ORM path).

    Args:
        station_id: The station number/ID

    Returns:
        JSON with available bikes, available stands, and status
        HTTP 404 if station not found
    """
    try:
        availability = BikeService.get_latest_availability(station_id)
        if not availability:
            return jsonify(error="Station not found"), 404
        return jsonify(availability), 200
    except Exception as e:
        logger.error(f"Error fetching availability for station {station_id}: {e}")
        return jsonify(error="Failed to fetch availability"), 500


# ============================================================================
# Weather Endpoints
# ============================================================================

@api_bp.route("/weather/latest", methods=["GET"])
def api_weather_latest():
    """
    Most recent weather snapshot from the database.
    Used by the map sidebar weather widget.

    Returns:
        JSON object with all weather fields, or {} if no data yet
    """
    try:
        record = (
            db.session.query(WeatherCurrent)
            .order_by(WeatherCurrent.dt_unix.desc())
            .first()
        )
        if not record:
            return jsonify({}), 200

        row = record.__dict__.copy()
        row.pop("_sa_instance_state", None)
        if row.get("dt_utc") and hasattr(row["dt_utc"], "isoformat"):
            row["dt_utc"] = row["dt_utc"].isoformat()
        return jsonify(row), 200
    except Exception as e:
        logger.error(f"Error fetching latest weather: {e}")
        return jsonify(error="Failed to fetch latest weather"), 500


@api_bp.route("/weather", methods=["GET"])
def api_weather():
    """
    Paginated weather history from the database.

    Query params:
        limit (int, optional): Max records, 1–500, default 48

    Returns:
        JSON array of weather records, newest first
    """
    limit = request.args.get("limit", default=48, type=int)
    limit = max(1, min(limit, 500))

    try:
        records = (
            db.session.query(WeatherCurrent)
            .order_by(WeatherCurrent.dt_unix.desc())
            .limit(limit)
            .all()
        )
        rows = []
        for r in records:
            row = r.__dict__.copy()
            row.pop("_sa_instance_state", None)
            if row.get("dt_utc") and hasattr(row["dt_utc"], "isoformat"):
                row["dt_utc"] = row["dt_utc"].isoformat()
            rows.append(row)
        return jsonify(rows), 200
    except Exception as e:
        logger.error(f"Error fetching weather history: {e}")
        return jsonify(error="Failed to fetch weather"), 500

# ============================================================================
# PREDICTION ENDPOINTS (Machine Learning)
# ============================================================================

@api_bp.route("/predict", methods=["GET"])
def predict_availability():
    """
    Predict available bikes for a station at a specific date/time.
    Uses the trained ML model to forecast bike availability.

    Query Parameters:
        station_id (int, required): The station number/ID
        date (str, required): Date in format YYYY-MM-DD (e.g., "2025-04-15")
        time (str, required): Time in format HH:MM (e.g., "14:30")

    Returns:
        JSON object with prediction:
            {
                "station_id": 42,
                "station_name": "Parnell Square East",
                "date": "2025-04-15",
                "time": "14:30",
                "predicted_bikes": 12
            }

    HTTP Status Codes:
        200: Prediction successful
        400: Missing or invalid parameters
        404: Station not found
        503: Model not available / Service unavailable
        500: Internal server error

    Example:
        GET /api/predict?station_id=42&date=2025-04-15&time=14:30
    """
    # Extract query parameters
    station_id = request.args.get("station_id", type=int)
    date = request.args.get("date", type=str)
    time = request.args.get("time", type=str)
    
    # Validate required parameters
    if station_id is None or not date or not time:
        logger.warning(
            f"Missing required parameters. "
            f"station_id={station_id}, date={date}, time={time}"
        )
        return jsonify(
            error="Missing required parameters",
            required=["station_id (int)", "date (YYYY-MM-DD)", "time (HH:MM)"]
        ), 400
    
    # Validate station_id is positive
    if station_id <= 0:
        logger.warning(f"Invalid station_id: {station_id}")
        return jsonify(error="station_id must be a positive integer"), 400
    
    try:
        # Call prediction service
        prediction = PredictionService.predict(station_id, date, time)
        return jsonify(prediction), 200
        
    except ValueError as e:
        # Invalid date format or station not found
        logger.warning(f"Validation error for prediction request: {e}")
        return jsonify(error=str(e)), 400
        
    except RuntimeError as e:
        # Model not available or prediction service error
        logger.error(f"Runtime error during prediction: {e}")
        return jsonify(error="Prediction service unavailable"), 503
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error during prediction: {e}")
        return jsonify(error="Failed to generate prediction"), 500


# ============================================================================
# Live External API Endpoints
# ============================================================================

@api_bp.route("/live/bikes", methods=["GET"])
def api_live_bikes():
    """
    Proxy to JCDecaux live bikes API — bypasses the database for real-time data.

    Returns:
        JSON array of live station data from JCDecaux
        HTTP 500 if API key missing or request fails
    """
    try:
        data = JCDecauxService.get_live_bike_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching live bike data: {e}")
        return jsonify(error="Failed to fetch live bike data"), 500


@api_bp.route("/live/weather", methods=["GET"])
def api_live_weather():
    """
    Proxy to OpenWeather live weather API — bypasses the database for real-time data.

    Returns:
        JSON object with current Dublin weather from OpenWeather
        HTTP 500 if API key missing or request fails
    """
    try:
        data = WeatherService.get_live_weather_data()
        if not data:
            return jsonify(error="Weather data unavailable"), 503
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching live weather data: {e}")
        return jsonify(error="Failed to fetch live weather"), 500


# ============================================================================
# Error Handling (API-specific)
# ============================================================================

@api_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify(error="Bad request", detail=str(error)), 400


@api_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    return jsonify(error="Unauthorized"), 401


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors."""
    return jsonify(error="Method not allowed"), 405

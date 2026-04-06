# app/api/routes.py
"""
API blueprint - JSON endpoints for frontend and external consumers.

Responsibilities:
- Handle HTTP requests
- Call services for business logic
- Return JSON responses

Does NOT:
- Access database directly (services do)
- Handle business logic (services do)
- Manage sessions (main routes do)
"""

import logging
from datetime import datetime
from flask import jsonify, request
from app.api import api_bp
from app.services.bike_service import BikeService
from app.services.weather_service import WeatherService
from app.services.jcdecaux_service import JCDecauxService

logger = logging.getLogger(__name__)


# ============ ERROR HANDLERS ============

@api_bp.errorhandler(400)
def bad_request(e):
    """Handle malformed requests."""
    logger.warning(f"400 Bad Request: {e}")
    return jsonify(error="Bad request", message=str(e)), 400


@api_bp.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access attempts."""
    logger.warning(f"401 Unauthorized: {e}")
    return jsonify(error="Unauthorized", message="Authentication required"), 401


@api_bp.errorhandler(403)
def forbidden(e):
    """Handle forbidden access."""
    logger.warning(f"403 Forbidden: {e}")
    return jsonify(error="Forbidden", message="You do not have access to this resource"), 403


@api_bp.errorhandler(404)
def not_found(e):
    """Handle resource not found."""
    logger.warning(f"404 Not Found: {request.url}")
    return jsonify(error="Not found", message="The requested resource does not exist"), 404


@api_bp.errorhandler(405)
def method_not_allowed(e):
    """Handle disallowed HTTP methods."""
    logger.warning(f"405 Method Not Allowed: {request.method} {request.url}")
    return jsonify(error="Method not allowed", message=str(e)), 405


@api_bp.errorhandler(429)
def too_many_requests(e):
    """Handle rate limiting."""
    logger.warning(f"429 Too Many Requests: {request.remote_addr}")
    return jsonify(error="Too many requests", message="Rate limit exceeded. Please slow down."), 429


@api_bp.errorhandler(500)
def internal_server_error(e):
    """Handle unexpected server errors."""
    logger.error(f"500 Internal Server Error: {e}")
    return jsonify(error="Internal server error", message="An unexpected error occurred"), 500


@api_bp.errorhandler(503)
def service_unavailable(e):
    """Handle service unavailability."""
    logger.error(f"503 Service Unavailable: {e}")
    return jsonify(error="Service unavailable", message="The service is temporarily unavailable"), 503


# ============ HEALTH & STATUS ROUTES ============

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Basic liveness check - confirms API is reachable.

    Returns:
        200: API is up
    """
    return jsonify(
        status="ok",
        timestamp=datetime.utcnow().isoformat()
    ), 200


@api_bp.route("/status", methods=["GET"])
def status_check():
    """
    Deep status check - verifies all dependent services are reachable.

    Returns:
        200: All services healthy
        207: Some services degraded
        503: All services unavailable
    """
    results = {}
    degraded = False

    # Check database via BikeService
    try:
        stations = BikeService.get_all_stations()
        results["database"] = {
            "status": "ok",
            "station_count": len(stations)
        }
    except Exception as e:
        logger.error(f"Status check - database error: {e}")
        results["database"] = {"status": "unavailable", "error": str(e)}
        degraded = True

    # Check weather service
    try:
        weather = WeatherService.get_current_weather()
        results["weather_service"] = {
            "status": "ok" if weather else "unavailable"
        }
        if not weather:
            degraded = True
    except Exception as e:
        logger.error(f"Status check - weather service error: {e}")
        results["weather_service"] = {"status": "unavailable", "error": str(e)}
        degraded = True

    # Check JCDecaux live feed
    try:
        live = JCDecauxService.get_live_stations()
        results["jcdecaux_service"] = {
            "status": "ok" if live else "unavailable",
            "live_station_count": len(live) if live else 0
        }
        if not live:
            degraded = True
    except Exception as e:
        logger.error(f"Status check - JCDecaux error: {e}")
        results["jcdecaux_service"] = {"status": "unavailable", "error": str(e)}
        degraded = True

    all_down = all(v["status"] == "unavailable" for v in results.values())

    return jsonify(
        status="degraded" if degraded else "ok",
        timestamp=datetime.utcnow().isoformat(),
        services=results
    ), 503 if all_down else 207 if degraded else 200


# ============ STATION ROUTES ============

@api_bp.route("/stations", methods=["GET"])
def get_stations():
    """
    Fetch all bike stations from the database.

    Returns:
        200: List of all stations
        503: If service is unavailable
    """
    stations = BikeService.get_all_stations()

    if stations is None:
        logger.error("Failed to fetch stations - service returned None")
        return jsonify(error="Station data unavailable"), 503

    logger.debug(f"Returning {len(stations)} stations")
    return jsonify(stations=stations), 200


@api_bp.route("/stations/<int:station_id>", methods=["GET"])
def get_station(station_id: int):
    """
    Fetch a single station by ID.

    Args:
        station_id: Station number

    Returns:
        200: Station dict
        404: If station not found
    """
    station = BikeService.get_station_by_id(station_id)

    if not station:
        logger.warning(f"Station {station_id} not found")
        return jsonify(error="Station not found"), 404

    return jsonify(station=station), 200


# ============ AVAILABILITY ROUTES ============

@api_bp.route("/availability/<int:station_id>", methods=["GET"])
def get_availability(station_id: int):
    """
    Fetch availability history for a station.

    Args:
        station_id: Station number

    Query Params:
        limit (int): Max records to return (default 100)

    Returns:
        200: List of availability records
        404: If no data found for station
    """
    limit = request.args.get("limit", 100, type=int)
    records = BikeService.get_availability_history(station_id, limit=limit)

    if not records:
        logger.warning(f"No availability data found for station {station_id}")
        return jsonify(error="No data found"), 404

    logger.debug(f"Returning {len(records)} availability records for station {station_id}")
    return jsonify(available=records), 200


@api_bp.route("/availability/<int:station_id>/latest", methods=["GET"])
def get_latest_availability(station_id: int):
    """
    Fetch the most recent availability record for a station.

    Args:
        station_id: Station number

    Returns:
        200: Latest availability dict
        404: If no data found for station
    """
    record = BikeService.get_latest_availability(station_id)

    if not record:
        logger.warning(f"No latest availability found for station {station_id}")
        return jsonify(error="No data found"), 404

    return jsonify(available=record), 200


# ============ WEATHER ROUTES ============

@api_bp.route("/weather", methods=["GET"])
def get_weather():
    """
    Fetch current weather data.

    Returns:
        200: Weather data dict
        503: If weather service is unavailable
    """
    weather = WeatherService.get_current_weather()

    if not weather:
        logger.error("Weather service returned no data")
        return jsonify(error="Weather unavailable"), 503

    return jsonify(weather=weather), 200


# ============ LIVE DATA ROUTES ============

@api_bp.route("/live-stations", methods=["GET"])
def get_live_stations():
    """
    Fetch live station data directly from JCDecaux API.

    Returns:
        200: List of live station data
        503: If JCDecaux service is unavailable
    """
    data = JCDecauxService.get_live_stations()

    if data is None:
        logger.error("JCDecaux service returned no data")
        return jsonify(error="Live station data unavailable"), 503

    logger.debug(f"Returning {len(data)} live stations")
    return jsonify(stations=data), 200


# ============ PREDICTIONS (PLACEHOLDER) ============

@api_bp.route("/predictions/<int:station_id>", methods=["GET"])
def get_prediction(station_id: int):
    """
    Fetch bike availability prediction for a station.

    Args:
        station_id: Station number

    Query Params:
        hour (int): Target hour for prediction (0-23)
        day  (int): Target day of week (0=Monday, 6=Sunday)

    Returns:
        200: Prediction result
        501: Not yet implemented
    """
    # TODO: Wire up PredictionService once model is trained and integrated
    # hour = request.args.get("hour", type=int)
    # day  = request.args.get("day",  type=int)
    # result = PredictionService.predict(station_id, hour, day)
    # return jsonify(prediction=result), 200

    logger.info(f"Prediction requested for station {station_id} - not yet implemented")
    return jsonify(
        status="not_implemented",
        message="Predictions are coming soon.",
        station_id=station_id
    ), 501


@api_bp.route("/predictions/<int:station_id>/range", methods=["GET"])
def get_prediction_range(station_id: int):
    """
    Fetch hourly availability predictions across a full day for a station.

    Args:
        station_id: Station number

    Query Params:
        day (int): Target day of week (0=Monday, 6=Sunday)

    Returns:
        200: List of hourly predictions
        501: Not yet implemented
    """
    # TODO: Wire up PredictionService.predict_day_range(station_id, day)
    # day = request.args.get("day", type=int)
    # results = PredictionService.predict_day_range(station_id, day)
    # return jsonify(predictions=results), 200

    logger.info(f"Prediction range requested for station {station_id} - not yet implemented")
    return jsonify(
        status="not_implemented",
        message="Day range predictions are coming soon.",
        station_id=station_id
    ), 501

"""
API Blueprint - RESTful API endpoints for client applications.

All routes follow this pattern:
1. Validate input (path params, query params)
2. Call service(s)
3. Handle errors
4. Return JSON with appropriate status code

No business logic in this file - all services.
No database queries in this file - use services.
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from app.api import api_bp

logger = logging.getLogger(__name__)

# ============ STATION DATA ============

@api_bp.route("/stations", methods=["GET"])
def get_stations():
    """
    Fetch all bike stations from database.
    
    GET /api/stations
    
    Returns:
        JSON: { "stations": [...] }
        Status: 200 (success), 503 (service unavailable)
    """
    try:
        from app.services.bike_service import BikeService
        
        stations = BikeService.get_all_stations()
        
        return jsonify(stations=stations), 200

    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return jsonify(error="Could not fetch stations"), 503


@api_bp.route("/stations/<int:station_id>", methods=["GET"])
def get_station(station_id):
    """
    Fetch a single station by ID.
    
    GET /api/stations/42
    
    Args:
        station_id: Station number
    
    Returns:
        JSON: { "station": {...} }
        Status: 200 (success), 404 (not found), 503 (error)
    """
    # Input validation
    if not isinstance(station_id, int) or station_id <= 0:
        return jsonify(error="Invalid station ID"), 400
    
    try:
        from app.services.bike_service import BikeService
        
        station = BikeService.get_station_by_id(station_id)
        
        if not station:
            return jsonify(error="Station not found"), 404
        
        return jsonify(station=station), 200

    except Exception as e:
        logger.error(f"Error fetching station {station_id}: {e}")
        return jsonify(error="Could not fetch station"), 503


# ============ AVAILABILITY DATA ============

@api_bp.route("/availability/<int:station_id>", methods=["GET"])
def get_availability(station_id):
    """
    Fetch recent availability history for a station.
    
    GET /api/availability/42
    
    Query params:
        limit: Max records (default 100, max 1000)
    
    Args:
        station_id: Station number
    
    Returns:
        JSON: { "available": [...] }
        Status: 200, 404 (no data), 503 (error)
    """
    # Input validation
    if not isinstance(station_id, int) or station_id <= 0:
        return jsonify(error="Invalid station ID"), 400
    
    # Get and validate limit param
    try:
        limit = int(request.args.get("limit", 100))
        limit = min(limit, 1000)  # Cap at 1000 records
        limit = max(limit, 1)
    except ValueError:
        return jsonify(error="Invalid limit parameter"), 400
    
    try:
        from app.services.bike_service import BikeService
        
        records = BikeService.get_availability_history(station_id, limit)
        
        if not records:
            return jsonify(error="No availability data for this station"), 404
        
        return jsonify(available=records), 200

    except Exception as e:
        logger.error(f"Error fetching availability {station_id}: {e}")
        return jsonify(error="Could not fetch availability data"), 503


@api_bp.route("/availability/<int:station_id>/latest", methods=["GET"])
def get_latest_availability(station_id):
    """
    Fetch the most recent availability record for a station.
    
    GET /api/availability/42/latest
    
    Args:
        station_id: Station number
    
    Returns:
        JSON: { "available": {...} }
        Status: 200, 404 (no data), 503 (error)
    """
    if not isinstance(station_id, int) or station_id <= 0:
        return jsonify(error="Invalid station ID"), 400
    
    try:
        from app.services.bike_service import BikeService
        
        records = BikeService.get_availability_history(station_id, limit=1)
        
        if not records:
            return jsonify(error="No availability data"), 404
        
        return jsonify(available=records[0]), 200

    except Exception as e:
        logger.error(f"Error fetching latest availability {station_id}: {e}")
        return jsonify(error="Could not fetch availability"), 503


# ============ LIVE EXTERNAL DATA ============

@api_bp.route("/bikes/live", methods=["GET"])
def live_bikes():
    """
    Return live bike station data from JCDecaux API.
    
    GET /api/bikes/live
    
    Returns:
        JSON: Array of live station data from JCDecaux
        Status: 200, 503 (API unavailable)
    """
    try:
        from app.services.jcdecaux_service import get_live_bike_data
        
        data = get_live_bike_data()
        
        # Even if empty, return 200 - the service handles errors
        return jsonify(data), 200

    except Exception as e:
        logger.error(f"Error fetching live bike data: {e}")
        return jsonify(error="Could not fetch live bike data", data=[]), 503


@api_bp.route("/weather/live", methods=["GET"])
def live_weather():
    """
    Return live weather data from OpenWeather API.
    
    GET /api/weather/live
    
    Returns:
        JSON: Current Dublin weather
        Status: 200, 503 (API unavailable)
    """
    try:
        from app.services.weather_service import get_live_weather_data
        
        data = get_live_weather_data()
        
        return jsonify(data), 200

    except Exception as e:
        logger.error(f"Error fetching live weather: {e}")
        return jsonify(error="Could not fetch weather data", data={}), 503


# ============ PREDICTIONS (PLACEHOLDER) ============

@api_bp.route("/predict/<int:station_id>", methods=["GET"])
def predict(station_id):
    """
    Predict available bikes at a station (placeholder).
    
    GET /api/predict/42
    
    Args:
        station_id: Station number
    
    Returns:
        JSON: Prediction data (currently placeholder)
        Status: 200, 503 (error)
    
    TODO: Integrate with ML model when ready
    """
    if not isinstance(station_id, int) or station_id <= 0:
        return jsonify(error="Invalid station ID"), 400
    
    try:
        # TODO: Load ML model and make prediction
        # from app.services.prediction_service import PredictionService
        # prediction = PredictionService.predict_availability(station_id)
        
        # For now, return placeholder
        return jsonify({
            "station_id": station_id,
            "prediction": None,
            "confidence": 0.0,
            "message": "Prediction service not yet implemented"
        }), 200

    except Exception as e:
        logger.error(f"Prediction error for station {station_id}: {e}")
        return jsonify(error="Prediction service unavailable"), 503


@api_bp.route("/predict/<int:station_id>/<timeframe>", methods=["GET"])
def predict_timeframe(station_id, timeframe):
    """
    Predict available bikes for a specific timeframe (placeholder).
    
    GET /api/predict/42/1h
    
    Args:
        station_id: Station number
        timeframe: "1h", "24h", or "7d"
    
    Returns:
        JSON: Timeframe prediction
        Status: 200, 400 (invalid timeframe), 503 (error)
    
    TODO: Implement when ML model is ready
    """
    # Input validation
    if not isinstance(station_id, int) or station_id <= 0:
        return jsonify(error="Invalid station ID"), 400
    
    valid_timeframes = ["1h", "24h", "7d"]
    if timeframe not in valid_timeframes:
        return jsonify(
            error=f"Invalid timeframe. Must be one of {valid_timeframes}"
        ), 400
    
    try:
        # TODO: Implement timeframe prediction
        return jsonify({
            "station_id": station_id,
            "timeframe": timeframe,
            "predictions": [],
            "message": "Timeframe predictions not yet implemented"
        }), 200

    except Exception as e:
        logger.error(f"Timeframe prediction error: {e}")
        return jsonify(error="Prediction service unavailable"), 503


# ============ HEALTH & STATUS ============

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring.
    
    GET /api/health
    
    Returns:
        JSON: { "status": "healthy", "database": "connected" }
        Status: 200 (healthy), 503 (problems)
    """
    try:
        from sqlalchemy import text
        
        # Test database connection
        current_app.db_session.execute(text("SELECT 1"))
        
        return jsonify(
            status="healthy",
            database="connected"
        ), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify(
            status="unhealthy",
            database="disconnected",
            error=str(e)
        ), 503


# ============ ERROR HANDLERS (For API blueprint only) ============

@api_bp.errorhandler(404)
def api_not_found(e):
    """Handle 404 errors in API."""
    return jsonify(error="Endpoint not found"), 404


@api_bp.errorhandler(405)
def api_method_not_allowed(e):
    """Handle 405 errors in API."""
    return jsonify(error="Method not allowed"), 405


@api_bp.errorhandler(500)
def api_internal_error(e):
    """Handle 500 errors in API."""
    logger.error(f"Internal API error: {e}")
    return jsonify(error="Internal server error"), 500

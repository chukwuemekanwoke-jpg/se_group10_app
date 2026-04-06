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
- GET /api/health — Health check for load balancers
- GET /api/stations — List all bike stations
- GET /api/stations/<id> — Get specific station details
- GET /api/availability/<station_id> — Get current bike availability
- GET /api/weather — Get current Dublin weather
- Other endpoints as defined below
"""

from flask import jsonify, request
from app.api import api_bp
from app.services import BikeService, JCDecauxService, WeatherService
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Health Check Endpoint (for load balancers & monitoring)
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
    Retrieve all Dublin Bikes stations.
    
    Returns:
        JSON array of station objects
        Each station includes: id, name, address, lat, lng, capacity, status
    """
    try:
        stations = BikeService.get_all_stations()
        return jsonify(stations=stations), 200 
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
        station = BikeService.get_station(station_id)
        if not station:
            return jsonify(error="Station not found"), 404
        return jsonify(station), 200
    except Exception as e:
        logger.error(f"Error fetching station {station_id}: {e}")
        return jsonify(error="Failed to fetch station"), 500


# ============================================================================
# Availability Endpoints
# ============================================================================

@api_bp.route("/availability/<int:station_id>", methods=["GET"])
def get_station_availability(station_id):
    """
    Get current bike availability for a specific station.
    
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

@api_bp.route("/weather", methods=["GET"])
def get_weather():
    """
    Get current Dublin weather.
    
    Returns:
        JSON with temperature, humidity, wind speed, conditions
        HTTP 500 if weather service unavailable
    """
    try:
        weather = WeatherService.get_current_weather()
        if not weather:
            return jsonify(error="Weather data unavailable"), 503
        return jsonify(weather), 200
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return jsonify(error="Failed to fetch weather"), 500


# ============================================================================
# Error Handling (API-specific)
# ============================================================================

@api_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify(error="Bad request"), 400


@api_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    return jsonify(error="Unauthorized"), 401


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors."""
    return jsonify(error="Method not allowed"), 405

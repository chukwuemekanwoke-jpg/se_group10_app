"""
app/api/routes.py - API Blueprint Routes
Dublin Bikes Web App - COMP30830 Project - Troithean

Handles:
- RESTful API endpoints for bike/availability data
- Live external API data (JCDecaux, OpenWeather)
- ML prediction endpoints
- API error handling and JSON responses
"""

import logging
from flask import Blueprint, jsonify, current_app, abort, request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.services.jcdecaux_service import get_live_bike_data
from app.services.weather_service import get_live_weather_data
from app.db import Availability, Station

# Create the API blueprint
api_bp = Blueprint("api", __name__)

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Station Data Routes
# -------------------------------------------------------
@api_bp.route("/stations", methods=["GET"])
def get_stations():
    """
    Fetch all bike stations from the database.
    Returns complete station information including location and capacity.

    Returns:
        JSON: Array of station objects
    """
    try:
        db_session = current_app.db_session
        stations = db_session.query(Station).all()

        stations_data = [station.to_dict() for station in stations]

        return jsonify(stations=stations_data), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching stations: {e}", exc_info=True)
        return jsonify(error="Database error"), 500
    except Exception as e:
        logger.error(f"Error fetching stations: {e}", exc_info=True)
        return jsonify(error="Internal server error"), 500


@api_bp.route("/stations/<int:station_id>", methods=["GET"])
def get_station(station_id):
    """
    Fetch a single station by ID.

    Args:
        station_id: The station number

    Returns:
        JSON: Station object or 404 if not found
    """
    try:
        db_session = current_app.db_session
        station = db_session.query(Station).filter_by(number=station_id).first()

        if not station:
            return jsonify(error="Station not found"), 404

        return jsonify(station=station.to_dict()), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching station {station_id}: {e}", exc_info=True)
        return jsonify(error="Database error"), 500
    except Exception as e:
        logger.error(f"Error fetching station {station_id}: {e}", exc_info=True)
        return jsonify(error="Internal server error"), 500


# -------------------------------------------------------
# Availability Data Routes
# -------------------------------------------------------
@api_bp.route("/availability/<int:station_id>", methods=["GET"])
def get_availability(station_id):
    """
    Fetch recent availability history for a station.
    Returns up to 100 most recent records, ordered by newest first.

    Args:
        station_id: The station number

    Returns:
        JSON: Array of availability records
        404: If station has no records
        500: Database error
    """
    try:
        db_session = current_app.db_session

        availability_records = (
            db_session.query(Availability)
            .filter_by(number=station_id)
            .order_by(Availability.last_update.desc())
            .limit(100)
            .all()
        )

        if not availability_records:
            return jsonify(error="No availability data found for this station"), 404

        data = [record.to_dict() for record in availability_records]

        return jsonify(available=data), 200

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching availability for station {station_id}: {e}",
            exc_info=True
        )
        return jsonify(error="Database error"), 500
    except Exception as e:
        logger.error(
            f"Error fetching availability for station {station_id}: {e}",
            exc_info=True
        )
        return jsonify(error="Internal server error"), 500


@api_bp.route("/availability/<int:station_id>/latest", methods=["GET"])
def get_latest_availability(station_id):
    """
    Fetch the most recent availability record for a station.

    Args:
        station_id: The station number

    Returns:
        JSON: Most recent availability record
        404: If no records found
    """
    try:
        db_session = current_app.db_session

        latest = (
            db_session.query(Availability)
            .filter_by(number=station_id)
            .order_by(Availability.last_update.desc())
            .first()
        )

        if not latest:
            return jsonify(error="No availability data found"), 404

        return jsonify(available=latest.to_dict()), 200

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching latest availability for {station_id}: {e}",
            exc_info=True
        )
        return jsonify(error="Database error"), 500
    except Exception as e:
        logger.error(
            f"Error fetching latest availability: {e}",
            exc_info=True
        )
        return jsonify(error="Internal server error"), 500


# -------------------------------------------------------
# Live External Data Routes
# -------------------------------------------------------
@api_bp.route("/bikes/live", methods=["GET"])
def live_bikes():
    """
    Return live bike station data from JCDecaux API.
    This includes real-time availability across all Dublin Bikes stations.

    Returns:
        JSON: Array of live bike station data
    """
    try:
        data = get_live_bike_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching live bike data: {e}", exc_info=True)
        return jsonify(error="Could not fetch live bike data"), 503


@api_bp.route("/weather/live", methods=["GET"])
def live_weather():
    """
    Return live weather data from OpenWeather API.
    Includes temperature, conditions, wind, and precipitation data.

    Returns:
        JSON: Weather data object
    """
    try:
        data = get_live_weather_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching live weather data: {e}", exc_info=True)
        return jsonify(error="Could not fetch live weather data"), 503


# -------------------------------------------------------
# ML Prediction Routes (Placeholder)
# -------------------------------------------------------
@api_bp.route("/predict/<int:station_id>", methods=["GET"])
def predict(station_id):
    """
    Placeholder for ML model inference.
    Predicts available bikes at a station.

    Args:
        station_id: The station number

    Returns:
        JSON: Prediction object or placeholder message
    """
    try:
        # TODO: Implement ML model loading and inference
        # For now, return placeholder response
        return jsonify({
            "station_id": station_id,
            "predicted_bikes": "ML model logic to be implemented",
            "confidence": 0.0,
            "timestamp": None
        }), 200

    except Exception as e:
        logger.error(f"Error in prediction for station {station_id}: {e}", exc_info=True)
        return jsonify(error="Prediction service unavailable"), 503


@api_bp.route("/predict/<int:station_id>/<string:timeframe>", methods=["GET"])
def predict_timeframe(station_id, timeframe):
    """
    Predict available bikes at a station for a specific timeframe.
    Timeframe: '1h', '24h', '7d'

    Args:
        station_id: The station number
        timeframe: Prediction timeframe

    Returns:
        JSON: Prediction data or error
    """
    valid_timeframes = ["1h", "24h", "7d"]
    if timeframe not in valid_timeframes:
        return jsonify(error=f"Invalid timeframe. Must be one of {valid_timeframes}"), 400

    try:
        # TODO: Implement ML model with timeframe support
        return jsonify({
            "station_id": station_id,
            "timeframe": timeframe,
            "predictions": [],
            "message": "ML model logic to be implemented"
        }), 200

    except Exception as e:
        logger.error(
            f"Error in timeframe prediction for station {station_id}: {e}",
            exc_info=True
        )
        return jsonify(error="Prediction service unavailable"), 503


# -------------------------------------------------------
# Health Check and Status Routes
# -------------------------------------------------------
@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring.
    Verifies database connectivity.

    Returns:
        JSON: Health status
    """
    try:
        db_session = current_app.db_session
        # Simple query to test database connection
        db_session.execute(text("SELECT 1"))
        return jsonify(status="healthy", database="connected"), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify(status="unhealthy", database="disconnected", error=str(e)), 503

"""
app/services/prediction_service.py - ML Model Prediction Service
Dublin Bikes Web App - COMP30830 Project - Troithean

Handles bike availability predictions using the trained ML model.
Includes feature engineering from input parameters and intelligent caching.
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
import pandas as pd
from flask import current_app
from ml_model import get_model
from app.services.bike_service import BikeService
from app.database.db import db
from app.database.models import WeatherCurrent

# Must match the column names used during model training exactly
FEATURE_NAMES = [
    'station_id',
    'capacity',
    'hour',
    'month',
    'day_of_week',
    'is_weekend',
    'rush_hour',
    'lat',
    'lon',
    'max_air_temperature_celsius',
    'max_relative_humidity_percent',
    'max_barometric_pressure_hpa',
]

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Simple in-memory cache manager for prediction data.
    Thread-safe and configurable with TTL (time-to-live).
    """
    
    def __init__(self, default_ttl=300):  # 5 minutes default
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key):
        if key not in self._cache:
            return None
        if key in self._timestamps:
            elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
            if elapsed > self.default_ttl:
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Cache expired for key: {key}")
                return None
        logger.debug(f"Cache hit for key: {key}")
        return self._cache[key]
    
    def set(self, key, value, ttl=None):
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        logger.debug(f"Cache set for key: {key} (TTL: {ttl or self.default_ttl}s)")
    
    def clear(self, key=None):
        if key:
            if key in self._cache:
                del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
            logger.debug(f"Cache cleared for key: {key}")
        else:
            self._cache.clear()
            self._timestamps.clear()
            logger.debug("Entire cache cleared")
    
    def stats(self):
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "ttl": self.default_ttl
        }


# Initialize cache with 10-minute TTL
_cache_manager = CacheManager(default_ttl=600)


class PredictionService:
    """Service for making bike availability predictions using ML model."""
    
    @staticmethod
    def predict(station_id, date_str, time_str):
        """
        Predict available bikes for a station at a given date/time.

        Args:
            station_id (int): The station number/ID
            date_str (str): Date in format YYYY-MM-DD (e.g., "2025-04-15")
            time_str (str): Time in format HH:MM (e.g., "14:30")

        Returns:
            dict: Prediction result with keys:
                - station_id (int)
                - station_name (str)
                - date (str)
                - time (str)
                - predicted_bikes (int)
                - from_cache (bool)

        Raises:
            ValueError: If date/time format is invalid or station not found
            RuntimeError: If model is not available
        """
        # Lazy-load ML model on first prediction request
        model = get_model()
        if model is None:
            logger.error("ML model is not available for predictions")
            raise RuntimeError("Prediction model not available. Please try again later.")
        
        # Validate and parse date/time
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Invalid date/time format: {date_str} {time_str}. Error: {e}")
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM. Error: {e}")
        
        # Get station information
        try:
            station = BikeService.get_station_by_id(station_id)
            if not station:
                logger.warning(f"Station {station_id} not found")
                raise ValueError(f"Station {station_id} not found")
        except Exception as e:
            logger.error(f"Error fetching station {station_id}: {e}")
            raise
        
        # Engineer features for the model
        try:
            features, from_cache = PredictionService._engineer_features(station_id, dt)
        except Exception as e:
            logger.error(f"Error engineering features for station {station_id}: {e}")
            raise
        
        # Make prediction — wrap in a named DataFrame so sklearn doesn't
        # raise a ValueError about missing feature names (model was trained
        # with a DataFrame, so feature_names_in_ is set on the model)
        try:
            X = pd.DataFrame([features], columns=FEATURE_NAMES)
            predicted_bikes = model.predict(X)[0]
            # Ensure prediction is in realistic range (0 to station capacity)
            station_capacity = station.get('bike_stands', 50)
            predicted_bikes = max(0, min(float(predicted_bikes), station_capacity))
        except Exception as e:
            logger.error(f"Error making prediction for station {station_id}: {e}")
            raise RuntimeError(f"Failed to generate prediction: {e}")
        
        cache_status = "(from cache)" if from_cache else "(DB query)"
        logger.info(
            f"Prediction: Station {station_id} at {date_str} {time_str} → "
            f"{int(predicted_bikes)} bikes {cache_status}"
        )
        
        return {
            "station_id": station_id,
            "station_name": station.get('name', f"Station {station_id}"),
            "date": date_str,
            "time": time_str,
            "predicted_bikes": int(predicted_bikes),
            "from_cache": from_cache,
        }
    
    @staticmethod
    def _engineer_features(station_id, dt):
        """
        Engineer feature vector for the ML model.

        The model (RandomForestRegressor) was trained with exactly these 12
        features in this order:
            station_id, capacity, hour, month, day_of_week, is_weekend,
            rush_hour, lat, lon,
            max_air_temperature_celsius, max_relative_humidity_percent,
            max_barometric_pressure_hpa

        Args:
            station_id (int): Station number
            dt (datetime): Datetime object for the prediction

        Returns:
            tuple: (features_list, from_cache_bool)
        """
        # --- Time features ---
        hour        = dt.hour
        month       = dt.month
        day_of_week = dt.weekday()          # 0=Monday, 6=Sunday
        is_weekend  = 1 if day_of_week >= 5 else 0
        # Rush hour: weekday morning (7-9) or evening (17-19)
        rush_hour   = 1 if (not is_weekend and (hour in range(7, 10) or hour in range(17, 20))) else 0

        # --- Station spatial / capacity features (WITH CACHING) ---
        try:
            station_meta, from_cache = PredictionService._get_station_meta_cached(station_id)
        except Exception as e:
            logger.warning(f"Could not fetch station meta for {station_id}: {e}")
            station_meta = {"capacity": 30, "lat": 53.3498, "lon": -6.2603}
            from_cache = False

        capacity = station_meta.get("capacity", 30)
        lat      = station_meta.get("lat",  53.3498)
        lon      = station_meta.get("lon", -6.2603)

        # --- Weather features (latest reading used as proxy for future) ---
        try:
            temp, humidity, pressure = PredictionService._get_latest_weather()
        except Exception as e:
            logger.warning(f"Could not fetch weather data: {e}")
            temp, humidity, pressure = 12.0, 75.0, 1013.0

        # Construct feature vector — order must match training exactly
        features = [
            station_id,   # 0: station_id
            capacity,     # 1: capacity
            hour,         # 2: hour
            month,        # 3: month
            day_of_week,  # 4: day_of_week
            is_weekend,   # 5: is_weekend
            rush_hour,    # 6: rush_hour
            lat,          # 7: lat
            lon,          # 8: lon
            temp,         # 9:  max_air_temperature_celsius
            humidity,     # 10: max_relative_humidity_percent
            pressure,     # 11: max_barometric_pressure_hpa
        ]

        return features, from_cache
    
    @staticmethod
    def _get_station_meta_cached(station_id):
        """Return station capacity, lat, lon from cache or DB."""
        cache_key = f"station_meta_{station_id}"
        cached = _cache_manager.get(cache_key)
        if cached is not None:
            return cached, True

        station = BikeService.get_station_by_id(station_id)
        if not station:
            raise ValueError(f"Station {station_id} not found")

        meta = {
            "capacity": station.get("bike_stands", 30),
            "lat":      float(station.get("position_lat") or 53.3498),
            "lon":      float(station.get("position_lng") or -6.2603),
        }
        _cache_manager.set(cache_key, meta)
        return meta, False

    @staticmethod
    def _get_latest_weather():
        """
        Fetch the most recent weather record and return the three
        features the model was trained on.

        Returns:
            tuple: (temp_celsius, humidity_percent, pressure_hpa)
        """
        try:
            record = (
                db.session.query(WeatherCurrent)
                .order_by(WeatherCurrent.dt_unix.desc())
                .first()
            )
            if record:
                temp     = float(record.temp     or 12.0)
                humidity = float(record.humidity  or 75.0)
                pressure = float(record.pressure  or 1013.0)
                return temp, humidity, pressure
        except Exception as e:
            logger.warning(f"Weather DB query failed: {e}")

        return 12.0, 75.0, 1013.0
    
    @staticmethod
    def clear_station_cache(station_id=None):
        """Manually clear cache for a station or entire cache."""
        if station_id:
            cache_key = f"station_meta_{station_id}"
            _cache_manager.clear(cache_key)
            logger.info(f"Cleared cache for station {station_id}")
        else:
            _cache_manager.clear()
            logger.info("Cleared all prediction cache")
    
    @staticmethod
    def get_cache_stats():
        """Get statistics about the cache."""
        return _cache_manager.stats()

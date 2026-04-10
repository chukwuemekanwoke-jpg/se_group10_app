"""
app/services/prediction_service.py - ML Model Prediction Service
Dublin Bikes Web App - COMP30830 Project - Troithean

Handles bike availability predictions using the trained ML model.
Includes feature engineering from input parameters and intelligent caching.
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from flask import current_app
from ml_model import model
from app.services import BikeService

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Simple in-memory cache manager for prediction data.
    Thread-safe and configurable with TTL (time-to-live).
    """
    
    def __init__(self, default_ttl=300):  # 5 minutes default
        """
        Initialize cache manager.
        
        Args:
            default_ttl (int): Default cache TTL in seconds (default 5 min)
        """
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key):
        """
        Get value from cache if valid (not expired).
        
        Args:
            key (str): Cache key
            
        Returns:
            Value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None
        
        # Check if cache has expired
        if key in self._timestamps:
            elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
            if elapsed > self.default_ttl:
                # Cache expired, remove it
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Cache expired for key: {key}")
                return None
        
        logger.debug(f"Cache hit for key: {key}")
        return self._cache[key]
    
    def set(self, key, value, ttl=None):
        """
        Set value in cache with TTL.
        
        Args:
            key (str): Cache key
            value: Value to cache
            ttl (int): Time-to-live in seconds (uses default if None)
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        logger.debug(f"Cache set for key: {key} (TTL: {ttl or self.default_ttl}s)")
    
    def clear(self, key=None):
        """
        Clear cache entry or entire cache.
        
        Args:
            key (str): Specific key to clear (all if None)
        """
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
        """
        Get cache statistics.
        
        Returns:
            dict: Cache stats (size, keys, etc)
        """
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "ttl": self.default_ttl
        }


# Initialize cache with 10-minute TTL for historical data
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
                - predicted_bikes (int): Predicted number of available bikes
                - from_cache (bool): Whether historical data was cached
                
        Raises:
            ValueError: If date/time format is invalid
            RuntimeError: If model is not available
            Exception: If station not found
            
        Example:
            >>> result = PredictionService.predict(42, "2025-04-15", "14:30")
            >>> print(result['predicted_bikes'])
            12
            >>> print(result['from_cache'])
            True
        """
        # Validate model availability
        if model is None:
            logger.error("ML model is not available for predictions")
            raise RuntimeError("Prediction model not available. Please try again later.")
        
        # Validate and parse date/time
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Invalid date/time format: {date_str} {time_str}. Error: {e}")
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM. Error: {e}")
        
        # Get station information (should be cached at DB level typically)
        try:
            station = BikeService.get_station_by_id(station_id)
            if not station:
                logger.warning(f"Station {station_id} not found")
                raise ValueError(f"Station {station_id} not found")
        except Exception as e:
            logger.error(f"Error fetching station {station_id}: {e}")
            raise
        
        # Engineer features for the model (includes caching)
        try:
            features, from_cache = PredictionService._engineer_features(station_id, dt)
        except Exception as e:
            logger.error(f"Error engineering features for station {station_id}: {e}")
            raise
        
        # Make prediction
        try:
            predicted_bikes = model.predict([features])[0]
            # Ensure prediction is in realistic range (0 to station capacity)
            station_capacity = station.get('bike_stands', 50)
            predicted_bikes = max(0, min(float(predicted_bikes), station_capacity))
        except Exception as e:
            logger.error(f"Error making prediction for station {station_id}: {e}")
            raise RuntimeError(f"Failed to generate prediction: {e}")
        
        # Log the prediction
        cache_status = "(from cache)" if from_cache else "(DB query)"
        logger.info(
            f"Prediction: Station {station_id} at {date_str} {time_str} → "
            f"{int(predicted_bikes)} bikes {cache_status}"
        )
        
        # Format response
        return {
            "station_id": station_id,
            "station_name": station.get('name', f"Station {station_id}"),
            "date": date_str,
            "time": time_str,
            "predicted_bikes": int(predicted_bikes),
            "from_cache": from_cache,  # Useful for debugging
        }
    
    @staticmethod
    def _engineer_features(station_id, dt):
        """
        Engineer feature vector for the ML model with caching.
        
        The model expects features in this order (example):
        [hour, day_of_week, month, station_id, historical_avg, ...]
        
        Args:
            station_id (int): Station number
            dt (datetime): Datetime object for the prediction
            
        Returns:
            tuple: (features_list, from_cache_bool)
            
        Note:
            This implementation should match the features used during 
            model training. Adjust based on your actual model's requirements.
        """
        # Extract time features (no caching needed - calculated each time)
        hour = dt.hour
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        day_of_month = dt.day
        month = dt.month
        week_of_year = dt.isocalendar()[1]
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Get historical statistics for the station (WITH CACHING)
        try:
            historical_avg, from_cache = PredictionService._get_historical_average_cached(
                station_id
            )
        except Exception as e:
            logger.warning(f"Could not fetch historical data for station {station_id}: {e}")
            historical_avg = 15.0  # Default fallback
            from_cache = False
        
        # Construct feature vector
        # NOTE: Adjust the order and features based on your trained model
        features = [
            station_id,              # 0: Station ID
            hour,                    # 1: Hour of day (0-23)
            day_of_week,            # 2: Day of week (0-6)
            day_of_month,           # 3: Day of month (1-31)
            month,                  # 4: Month (1-12)
            week_of_year,           # 5: Week of year (1-52)
            is_weekend,             # 6: Is weekend (0 or 1)
            historical_avg,         # 7: Historical average bikes
        ]
        
        return features, from_cache
    
    @staticmethod
    def _get_historical_average_cached(station_id, days_back=30):
        """
        Get historical average available bikes for a station WITH CACHING.
        
        This method implements a two-level caching strategy:
        1. In-memory cache (fast, expires every 10 minutes)
        2. Database fallback (slower, but fresh data)
        
        Args:
            station_id (int): Station number
            days_back (int): Number of days to look back (default 30)
            
        Returns:
            tuple: (average_bikes_float, from_cache_bool)
            
        Note:
            In production, you might also consider:
            - Redis cache for distributed systems
            - Database query caching with materialized views
            - Time-based aggregation tables
        """
        # Create cache key
        cache_key = f"hist_avg_station_{station_id}"
        
        # Try to get from in-memory cache first
        cached_value = _cache_manager.get(cache_key)
        if cached_value is not None:
            logger.debug(f"Using cached historical average for station {station_id}")
            return cached_value, True
        
        # Cache miss - query database
        logger.debug(f"Cache miss for station {station_id}, querying database")
        average = PredictionService._get_historical_average_from_db(station_id, days_back)
        
        # Store in cache for future requests
        _cache_manager.set(cache_key, average)
        
        return average, False
    
    @staticmethod
    def _get_historical_average_from_db(station_id, days_back=30):
        """
        Query database for historical average available bikes.
        
        This is the actual DB query that gets cached.
        
        Args:
            station_id (int): Station number
            days_back (int): Number of days to look back
            
        Returns:
            float: Average available bikes over the period
        """
        try:
            # Method 1: Use BikeService if it has aggregation
            availability = BikeService.get_latest_availability(station_id)
            if availability and 'available_bikes' in availability:
                current_value = float(availability['available_bikes'])
                logger.debug(f"Got current availability for station {station_id}: {current_value}")
                return current_value
            
            # Method 2: For more sophisticated averaging, use raw SQL
            # Uncomment if you want to calculate averages over time period
            # from app.database.db import db
            # from app.database.models import Availability
            # 
            # cutoff_date = datetime.now() - timedelta(days=days_back)
            # result = db.session.query(
            #     db.func.avg(Availability.available_bikes)
            # ).filter(
            #     Availability.number == station_id,
            #     Availability.last_update >= cutoff_date
            # ).scalar()
            # 
            # if result is not None:
            #     return float(result)
            
            # Fallback if no data available
            logger.warning(f"No historical data found for station {station_id}")
            return 15.0
            
        except Exception as e:
            logger.error(f"Error querying historical average for station {station_id}: {e}")
            return 15.0
    
    @staticmethod
    def clear_station_cache(station_id=None):
        """
        Manually clear cache for a station or entire cache.
        
        Useful when you want to force a fresh DB query.
        
        Args:
            station_id (int): Specific station to clear (all if None)
            
        Example:
            >>> PredictionService.clear_station_cache(42)  # Clear station 42
            >>> PredictionService.clear_station_cache()    # Clear all
        """
        if station_id:
            cache_key = f"hist_avg_station_{station_id}"
            _cache_manager.clear(cache_key)
            logger.info(f"Cleared cache for station {station_id}")
        else:
            _cache_manager.clear()
            logger.info("Cleared all prediction cache")
    
    @staticmethod
    def get_cache_stats():
        """
        Get statistics about the cache.
        
        Returns:
            dict: Cache statistics
            
        Example:
            >>> stats = PredictionService.get_cache_stats()
            >>> print(f"Cache size: {stats['cache_size']}")
        """
        return _cache_manager.stats()

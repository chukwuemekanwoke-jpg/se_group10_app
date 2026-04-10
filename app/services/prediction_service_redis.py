"""
app/services/prediction_service_redis.py - Prediction Service with Redis Caching
Alternative implementation using Redis for distributed caching.

"""

import logging
import os
from datetime import datetime
from functools import wraps
from flask import current_app
from ml_model import model
from app.services import BikeService

logger = logging.getLogger(__name__)


def with_redis_cache(cache_key_func, timeout=600):
    """
    Decorator to add Redis caching to any function.
    
    Args:
        cache_key_func: Function that generates cache key
        timeout: Cache TTL in seconds (default 10 min)
        
    Example:
        @with_redis_cache(
            cache_key_func=lambda station_id: f"hist_avg_{station_id}",
            timeout=600
        )
        def get_historical_average(station_id):
            return query_db(station_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache = current_app.extensions.get('cache')
                if not cache:
                    # Cache not available, call function directly
                    logger.warning("Cache not available, calling function directly")
                    return func(*args, **kwargs), False
                
                # Generate cache key
                cache_key = cache_key_func(*args, **kwargs)
                
                # Try to get from cache
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value, True
                
                # Cache miss - call function
                logger.debug(f"Cache miss: {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                cache.set(cache_key, result, timeout=timeout)
                logger.debug(f"Cached: {cache_key} (TTL: {timeout}s)")
                
                return result, False
                
            except Exception as e:
                logger.error(f"Cache error: {e}. Continuing without cache.")
                return func(*args, **kwargs), False
        
        return wrapper
    return decorator


class PredictionService:
    """Service for making bike availability predictions using Redis caching."""
    
    # Cache configuration
    CACHE_TTL = {
        'historical_avg': 600,      # 10 minutes
        'station_info': 3600,       # 1 hour
        'predictions': 300,         # 5 minutes
    }
    
    @staticmethod
    def predict(station_id, date_str, time_str):
        """
        Predict available bikes for a station at a given date/time.
        Uses Redis for caching historical data.
        
        Args:
            station_id (int): The station number/ID
            date_str (str): Date in format YYYY-MM-DD
            time_str (str): Time in format HH:MM
            
        Returns:
            dict: Prediction result with 'from_cache' flag
            
        Raises:
            ValueError: If date/time format is invalid
            RuntimeError: If model is not available
        """
        # Validate model
        if model is None:
            logger.error("ML model not available")
            raise RuntimeError("Prediction model not available. Please try again later.")
        
        # Validate and parse date/time
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Invalid date/time format: {date_str} {time_str}")
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM.")
        
        # Get station info
        try:
            station = BikeService.get_station_by_id(station_id)
            if not station:
                raise ValueError(f"Station {station_id} not found")
        except Exception as e:
            logger.error(f"Error fetching station: {e}")
            raise
        
        # Engineer features (uses caching)
        try:
            features, from_cache = PredictionService._engineer_features(station_id, dt)
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            raise
        
        # Make prediction
        try:
            predicted_bikes = model.predict([features])[0]
            station_capacity = station.get('bike_stands', 50)
            predicted_bikes = max(0, min(float(predicted_bikes), station_capacity))
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise RuntimeError(f"Failed to generate prediction: {e}")
        
        # Log
        cache_status = "(cached)" if from_cache else "(fresh)"
        logger.info(
            f"Prediction: Station {station_id} → {int(predicted_bikes)} bikes {cache_status}"
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
        Engineer features for the ML model with Redis caching.
        
        Returns:
            tuple: (features_list, from_cache_bool)
        """
        # Extract time features
        hour = dt.hour
        day_of_week = dt.weekday()
        day_of_month = dt.day
        month = dt.month
        week_of_year = dt.isocalendar()[1]
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Get historical average (uses Redis cache)
        historical_avg, from_cache = PredictionService._get_historical_average_redis(
            station_id
        )
        
        # Build feature vector
        features = [
            station_id,
            hour,
            day_of_week,
            day_of_month,
            month,
            week_of_year,
            is_weekend,
            historical_avg,
        ]
        
        return features, from_cache
    
    @staticmethod
    def _get_historical_average_redis(station_id):
        """
        Get historical average with Redis caching.
        
        Returns:
            tuple: (average_bikes_float, from_cache_bool)
        """
        try:
            cache = current_app.extensions.get('cache')
            if not cache:
                # No cache available, query DB directly
                avg = PredictionService._get_from_db(station_id)
                return avg, False
            
            # Create cache key
            cache_key = f"prediction:hist_avg:station_{station_id}"
            
            # Try to get from Redis
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Redis hit: {cache_key}")
                return float(cached_value), True
            
            # Cache miss - query database
            logger.debug(f"Redis miss: {cache_key}")
            avg = PredictionService._get_from_db(station_id)
            
            # Store in Redis with TTL
            cache.set(
                cache_key, 
                avg, 
                timeout=PredictionService.CACHE_TTL['historical_avg']
            )
            logger.debug(f"Stored in Redis: {cache_key}")
            
            return avg, False
            
        except Exception as e:
            logger.error(f"Redis caching error: {e}. Falling back to DB query.")
            avg = PredictionService._get_from_db(station_id)
            return avg, False
    
    @staticmethod
    def _get_from_db(station_id):
        """
        Query database for historical average bikes.
        This is the actual DB query that gets cached.
        
        Args:
            station_id (int): Station number
            
        Returns:
            float: Average available bikes
        """
        try:
            availability = BikeService.get_latest_availability(station_id)
            if availability and 'available_bikes' in availability:
                return float(availability['available_bikes'])
            return 15.0
        except Exception as e:
            logger.error(f"Error querying DB: {e}")
            return 15.0
    
    @staticmethod
    def invalidate_cache(station_id=None):
        """
        Manually invalidate Redis cache.
        
        Args:
            station_id (int): Specific station, or None for all
            
        Example:
            >>> PredictionService.invalidate_cache(42)  # Clear station 42
            >>> PredictionService.invalidate_cache()    # Clear all
        """
        try:
            cache = current_app.extensions.get('cache')
            if not cache:
                logger.warning("Cache not available")
                return False
            
            if station_id:
                cache_key = f"prediction:hist_avg:station_{station_id}"
                cache.delete(cache_key)
                logger.info(f"Invalidated cache for station {station_id}")
            else:
                # Clear all prediction-related keys
                # Note: This works with Redis but not all cache backends
                cache.clear()
                logger.info("Cleared entire prediction cache")
            
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    @staticmethod
    def get_cache_info():
        """
        Get cache statistics and info.
        
        Returns:
            dict: Cache statistics
        """
        try:
            cache = current_app.extensions.get('cache')
            if not cache:
                return {"status": "Cache not available"}
            
            # For Redis backend
            if hasattr(cache, 'cache') and hasattr(cache.cache, 'info'):
                redis_info = cache.cache.info()
                return {
                    "status": "Redis connected",
                    "used_memory": redis_info.get('used_memory_human', 'N/A'),
                    "connected_clients": redis_info.get('connected_clients', 'N/A'),
                    "total_commands": redis_info.get('total_commands_processed', 'N/A'),
                }
            
            return {"status": "Cache available but info unavailable"}
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"status": "Error", "error": str(e)}


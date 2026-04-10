"""
app/services/weather_service.py - OpenWeather API Service
Dublin Bikes Web App - COMP30830 Project - Troithean

Handles:
- Fetching live Dublin weather data from OpenWeather API
- API error handling and fallback logic
- Weather data formatting and processing
- Storing weather data to database
"""

import logging
import requests
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

# OpenWeather API endpoints
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
DUBLIN_CITY_ID = 2988507
REQUEST_TIMEOUT = 5  # seconds


class WeatherService:
    """Service class for interacting with the OpenWeather API."""

    @staticmethod
    def get_live_weather_data():
        """
        Fetch live Dublin weather data from OpenWeather API.
        Returns current weather conditions including temperature, wind, precipitation, etc.

        Returns:
            dict: Weather data object
            {}: Empty dict if API call fails

        Example response structure:
            {
                "coord": {"lon": -6.26, "lat": 53.35},
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain",
                        "icon": "10d"
                    }
                ],
                "main": {
                    "temp": 12.5,
                    "feels_like": 11.2,
                    "temp_min": 10.5,
                    "temp_max": 14.5,
                    "pressure": 1013,
                    "humidity": 75
                },
                "visibility": 10000,
                "wind": {
                    "speed": 4.5,
                    "deg": 240
                },
                "clouds": {"all": 90},
                "dt": 1234567890,
                "timezone": 3600,
                "id": 2988507,
                "name": "Dublin",
                "cod": 200
            }
        """
        try:
            api_key = current_app.config.get("OPENWEATHER_API_KEY")

            if not api_key:
                logger.warning("OPENWEATHER_API_KEY not configured")
                return {}

            # Build API request URL
            url = f"{OPENWEATHER_BASE_URL}/weather"
            params = {
                "q": "Dublin,IE",
                "appid": api_key,
                "units": "metric"  # Use Celsius
            }

            # Make API request
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            logger.info("Successfully fetched weather data from OpenWeather API")

            return data

        except requests.exceptions.Timeout:
            logger.error("OpenWeather API request timed out")
            return {}

        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to OpenWeather API")
            return {}

        except requests.exceptions.HTTPError as e:
            logger.error(f"OpenWeather API HTTP error: {e.response.status_code}")
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API request error: {e}")
            return {}

        except ValueError as e:
            logger.error(f"Error parsing OpenWeather API response: {e}")
            return {}

        except Exception as e:
            logger.error(f"Unexpected error fetching weather data: {e}", exc_info=True)
            return {}

    @staticmethod
    def get_weather_by_city_id(city_id):
        """
        Fetch weather data for a specific city by OpenWeather city ID.

        Args:
            city_id (int): OpenWeather city ID

        Returns:
            dict: Weather data
            {}: If API error or city not found
        """
        try:
            api_key = current_app.config.get("OPENWEATHER_API_KEY")

            if not api_key:
                logger.warning("OPENWEATHER_API_KEY not configured")
                return {}

            url = f"{OPENWEATHER_BASE_URL}/weather"
            params = {
                "id": city_id,
                "appid": api_key,
                "units": "metric"
            }

            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            logger.info(f"Successfully fetched weather data for city {city_id}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API error for city {city_id}: {e}")
            return {}

        except Exception as e:
            logger.error(f"Error fetching weather for city {city_id}: {e}", exc_info=True)
            return {}

    @staticmethod
    def get_weather_forecast():
        """
        Fetch 5-day weather forecast for Dublin.
        Uses the forecast API endpoint (requires API subscription).

        Returns:
            dict: Forecast data
            {}: If API call fails
        """
        try:
            api_key = current_app.config.get("OPENWEATHER_API_KEY")

            if not api_key:
                logger.warning("OPENWEATHER_API_KEY not configured")
                return {}

            url = f"{OPENWEATHER_BASE_URL}/forecast"
            params = {
                "q": "Dublin,IE",
                "appid": api_key,
                "units": "metric"
            }

            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            logger.info("Successfully fetched weather forecast from OpenWeather API")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather forecast API error: {e}")
            return {}

        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}", exc_info=True)
            return {}

    @staticmethod
    def save_weather_to_db(weather_data):
        """
        Save weather data to the database.
        Extracts relevant fields and creates a WeatherCurrent record.

        Args:
            weather_data (dict): Raw weather data from OpenWeather API

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            from app.database.models import WeatherCurrent
            from app.database.db import db

            if not weather_data:
                logger.warning("Cannot save empty weather data")
                return False

            # Extract weather data
            weather_record = WeatherCurrent(
                dt_unix=int(weather_data.get("dt", 0)),
                dt_utc=datetime.utcfromtimestamp(weather_data.get("dt", 0)),
                city_id=weather_data.get("id"),
                city_name=weather_data.get("name"),
                lat=weather_data.get("coord", {}).get("lat"),
                lon=weather_data.get("coord", {}).get("lon"),
                temp=weather_data.get("main", {}).get("temp"),
                feels_like=weather_data.get("main", {}).get("feels_like"),
                temp_min=weather_data.get("main", {}).get("temp_min"),
                temp_max=weather_data.get("main", {}).get("temp_max"),
                pressure=weather_data.get("main", {}).get("pressure"),
                humidity=weather_data.get("main", {}).get("humidity"),
                visibility=weather_data.get("visibility"),
                wind_speed=weather_data.get("wind", {}).get("speed"),
                wind_deg=weather_data.get("wind", {}).get("deg"),
                clouds_all=weather_data.get("clouds", {}).get("all"),
                rain_1h=weather_data.get("rain", {}).get("1h"),
                snow_1h=weather_data.get("snow", {}).get("1h"),
                weather_id=weather_data.get("weather", [{}])[0].get("id"),
                weather_main=weather_data.get("weather", [{}])[0].get("main"),
                weather_desc=weather_data.get("weather", [{}])[0].get("description"),
                weather_icon=weather_data.get("weather", [{}])[0].get("icon"),
            )

            db.session.add(weather_record)
            db.session.commit()

            logger.info("Weather data saved to database")

            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving weather data to database: {e}", exc_info=True)
            return False

    @staticmethod
    def parse_weather_summary(weather_data):
        """
        Parse and summarize weather data into a human-readable format.

        Args:
            weather_data (dict): Raw weather data from OpenWeather API

        Returns:
            dict: Summarized weather information
        """
        try:
            if not weather_data:
                return {}

            main = weather_data.get("main", {})
            weather = weather_data.get("weather", [{}])[0]
            wind = weather_data.get("wind", {})

            summary = {
                "city": weather_data.get("name"),
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "condition": weather.get("main"),
                "description": weather.get("description"),
                "humidity": main.get("humidity"),
                "wind_speed": wind.get("speed"),
                "wind_direction": wind.get("deg"),
                "clouds": weather_data.get("clouds", {}).get("all"),
                "visibility": weather_data.get("visibility"),
                "precipitation": weather_data.get("rain", {}).get("1h", 0) +
                                 weather_data.get("snow", {}).get("1h", 0)
            }

            return summary

        except Exception as e:
            logger.error(f"Error parsing weather summary: {e}", exc_info=True)
            return {}

"""
app/services/jcdecaux_service.py - JCDecaux API Service
Dublin Bikes Web App - COMP30830 Project - Troithean

Handles:
- Fetching live Dublin Bikes station data from JCDecaux API
- API error handling and fallback logic
- Data formatting and caching (optional)
"""

import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

# JCDecaux API endpoint for Dublin Bikes
JCDECAUX_BASE_URL = "https://api.jcdecaux.com/vls/v1"
DUBLIN_CONTRACT = "dublin"
REQUEST_TIMEOUT = 5  # seconds

class JCDecauxService:
    
def get_live_bike_data():
    """
    Fetch live Dublin Bikes station data from JCDecaux API.
    Returns real-time bike and stand availability for all Dublin stations.

    Returns:
        list: Array of station objects with live data
        []: Empty list if API call fails

    Example response structure:
        [
            {
                "number": 1,
                "name": "Stoneybatter",
                "address": "Stoneybatter, Dublin 7",
                "position": {"lat": 53.362, "lng": -6.277},
                "bike_stands": 30,
                "available_bikes": 15,
                "available_bike_stands": 15,
                "status": "OPEN",
                "last_update": 1234567890000
            },
            ...
        ]
    """
    try:
        api_key = current_app.config.get("JCDECAUX_API_KEY")

        if not api_key:
            logger.warning("JCDECAUX_API_KEY not configured")
            return []

        # Build API request URL
        url = f"{JCDECAUX_BASE_URL}/stations"
        params = {
            "contract": DUBLIN_CONTRACT,
            "apiKey": api_key
        }

        # Make API request
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        logger.info(f"Successfully fetched {len(data)} stations from JCDecaux API")

        return data

    except requests.exceptions.Timeout:
        logger.error("JCDecaux API request timed out")
        return []

    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to JCDecaux API")
        return []

    except requests.exceptions.HTTPError as e:
        logger.error(f"JCDecaux API HTTP error: {e.response.status_code}")
        return []

    except requests.exceptions.RequestException as e:
        logger.error(f"JCDecaux API request error: {e}")
        return []

    except ValueError as e:
        logger.error(f"Error parsing JCDecaux API response: {e}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error fetching live bike data: {e}", exc_info=True)
        return []


def get_station_by_id(station_id):
    """
    Fetch live data for a specific station from JCDecaux API.

    Args:
        station_id (int): Station number

    Returns:
        dict: Station data
        None: If station not found or API error
    """
    try:
        api_key = current_app.config.get("JCDECAUX_API_KEY")

        if not api_key:
            logger.warning("JCDECAUX_API_KEY not configured")
            return None

        url = f"{JCDECAUX_BASE_URL}/stations/{station_id}"
        params = {
            "contract": DUBLIN_CONTRACT,
            "apiKey": api_key
        }

        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        logger.info(f"Successfully fetched data for station {station_id}")

        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Station {station_id} not found")
        else:
            logger.error(f"JCDecaux API HTTP error: {e.response.status_code}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"JCDecaux API request error for station {station_id}: {e}")
        return None

    except Exception as e:
        logger.error(f"Error fetching live data for station {station_id}: {e}", exc_info=True)
        return None


def compare_db_with_live(db_stations, live_stations):
    """
    Compare database stations with live API data to identify changes.
    Useful for tracking real-time availability changes.

    Args:
        db_stations (list): Station data from database
        live_stations (list): Station data from JCDecaux API

    Returns:
        dict: Analysis of differences
    """
    try:
        db_map = {s["number"]: s for s in db_stations}
        live_map = {s["number"]: s for s in live_stations}

        changes = {
            "new_stations": [s for s in live_map.keys() if s not in db_map],
            "removed_stations": [s for s in db_map.keys() if s not in live_map],
            "availability_changes": []
        }

        # Check for availability changes
        for station_id in set(db_map.keys()) & set(live_map.keys()):
            db_bikes = db_map[station_id].get("available_bikes", 0)
            live_bikes = live_map[station_id].get("available_bikes", 0)

            if db_bikes != live_bikes:
                changes["availability_changes"].append({
                    "station_id": station_id,
                    "db_bikes": db_bikes,
                    "live_bikes": live_bikes
                })

        return changes

    except Exception as e:
        logger.error(f"Error comparing DB with live data: {e}", exc_info=True)
        return {}


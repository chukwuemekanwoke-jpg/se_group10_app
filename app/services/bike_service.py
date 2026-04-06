# app/services/bike_service.py
"""
Bike data service - handles database access for bike-related queries.
Depends on database models but abstracts the ORM.
"""

import logging
from typing import List, Dict, Optional
from app.database.db import db
from app.database.models import Station, Availability

logger = logging.getLogger(__name__)


class BikeService:
    """Encapsulates bike-related database operations."""

    @staticmethod
    def get_all_stations() -> List[Dict]:
        """
        Fetch all stations from the database.

        Returns:
            List of station dicts, or empty list on error
        """
        try:
            stations = db.session.query(Station).all()
            return [s.to_dict() for s in stations]

        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            return []

    @staticmethod
    def get_station_by_id(station_id: int) -> Optional[Dict]:
        """
        Fetch a single station by its ID.

        Args:
            station_id: Station number

        Returns:
            Station dict, or None if not found/error
        """
        try:
            station = db.session.query(Station).filter_by(number=station_id).first()
            return station.to_dict() if station else None

        except Exception as e:
            logger.error(f"Error fetching station {station_id}: {e}")
            return None

    @staticmethod
    def get_availability_history(station_id: int, limit: int = 100) -> List[Dict]:
        """
        Fetch recent availability records for a station.

        Args:
            station_id: Station number
            limit: Maximum records to return

        Returns:
            List of availability dicts, or empty list if not found/error
        """
        try:
            records = (
                db.session.query(Availability)
                .filter_by(number=station_id)
                .order_by(Availability.last_update.desc())
                .limit(limit)
                .all()
            )
            return [r.to_dict() for r in records]

        except Exception as e:
            logger.error(f"Error fetching availability for station {station_id}: {e}")
            return []

    @staticmethod
    def get_latest_availability(station_id: int) -> Optional[Dict]:
        """
        Fetch the most recent availability record for a station.

        Args:
            station_id: Station number

        Returns:
            Most recent availability dict, or None if not found
        """
        records = BikeService.get_availability_history(station_id, limit=1)
        return records[0] if records else None


# Test example (requires Flask context but no HTTP):
if __name__ == "__main__":
    from app import create_app

    app = create_app("development")
    with app.app_context():
        stations = BikeService.get_all_stations()
        print(f"Found {len(stations)} stations")

        station = BikeService.get_station_by_id(1)
        print(f"Station 1: {station}")

        avail = BikeService.get_availability_history(1, limit=5)
        print(f"Station 1 has {len(avail)} history records")

        latest = BikeService.get_latest_availability(1)
        print(f"Station 1 latest availability: {latest}")

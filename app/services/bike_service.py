"""
Bike data service - handles database access for bike-related queries.
Depends on database models but abstracts the ORM.
"""

import logging
from typing import List, Dict, Optional
from flask import current_app

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
            from app.database.models import Station
            
            stations = current_app.db_session.query(Station).all()
            
            return [
                {
                    "id": s.number,
                    "name": s.name,
                    "address": s.address,
                    "lat": s.position_lat,
                    "lng": s.position_lng,
                    "capacity": s.bike_stands
                }
                for s in stations
            ]
        
        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            return []
    
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
            from app.database.models import Availability
            from sqlalchemy import desc
            
            records = (
                current_app.db_session
                .query(Availability)
                .filter_by(number=station_id)
                .order_by(desc(Availability.last_update))
                .limit(limit)
                .all()
            )
            
            if not records:
                return []
            
            return [
                {
                    "timestamp": r.last_update.isoformat(),
                    "available_bikes": r.available_bikes,
                    "available_stands": r.available_bike_stands,
                    "status": r.status
                }
                for r in records
            ]
        
        except Exception as e:
            logger.error(f"Error fetching availability for station {station_id}: {e}")
            return []


# Test example (requires Flask context but no HTTP):
if __name__ == "__main__":
    from app import create_app
    
    app = create_app("development")
    with app.app_context():
        stations = BikeService.get_all_stations()
        print(f"Found {len(stations)} stations")
        
        avail = BikeService.get_availability_history(1, limit=5)
        print(f"Station 1 has {len(avail)} history records")

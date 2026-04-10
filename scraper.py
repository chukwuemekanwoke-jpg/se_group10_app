#!/usr/bin/env python3
"""
scraper.py - Hourly Data Scraper for Troithean Dublin Bikes App
COMP30830 Project - Troithean

Fetches live bike availability from JCDecaux and current weather from
OpenWeather, then writes both to the AWS RDS database.

Usage:
    Run manually (one-off):
        cd /home/ubuntu/se_group10_app
        source venv/bin/activate
        python scraper.py

    Scheduled via cron (every hour):
        0 * * * * cd /home/ubuntu/se_group10_app && \
            /home/ubuntu/se_group10_app/venv/bin/python scraper.py \
            >> /home/ubuntu/se_group10_app/logs/scraper.log 2>&1
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# ── Bootstrap ─────────────────────────────────────────────────────────────────
# Load .env BEFORE importing anything that reads environment variables
load_dotenv()

# Ensure project root is on the path so app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Default to production so DEBUG=False and SQL echo is off
os.environ.setdefault("FLASK_ENV", "production")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scraper")

# ── Imports (after path/env setup) ────────────────────────────────────────────
from app import create_app
from app.database.db import db
from app.database.models import Availability, WeatherCurrent
from app.services.jcdecaux_service import JCDecauxService
from app.services.weather_service import WeatherService


# ── Bike Availability Scraper ─────────────────────────────────────────────────

def scrape_bike_availability(app) -> int:
    """
    Fetch all Dublin Bikes station availability from JCDecaux and
    insert new records into the availability table.

    Skips records where the (number, last_update) primary key already
    exists to avoid duplicates.

    Returns:
        int: Number of new records inserted
    """
    with app.app_context():
        logger.info("Fetching live bike data from JCDecaux API...")
        stations = JCDecauxService.get_live_bike_data()

        if not stations:
            logger.warning("JCDecaux returned no data — skipping bike scrape.")
            return 0

        inserted = 0
        skipped = 0
        errors = 0
        now = datetime.utcnow()

        for s in stations:
            try:
                # JCDecaux returns last_update as milliseconds epoch timestamp
                raw_ts = s.get("last_update")
                last_update = (
                    datetime.utcfromtimestamp(raw_ts / 1000)
                    if raw_ts
                    else now
                )

                # (number, last_update) is the composite PK — skip if exists
                exists = (
                    db.session.query(Availability)
                    .filter_by(number=s["number"], last_update=last_update)
                    .first()
                )
                if exists:
                    skipped += 1
                    continue

                record = Availability(
                    number=s["number"],
                    last_update=last_update,
                    available_bikes=s.get("available_bikes"),
                    available_bike_stands=s.get("available_bike_stands"),
                    status=s.get("status"),
                )
                db.session.add(record)
                inserted += 1

            except Exception as e:
                logger.error(f"Error processing station {s.get('number', '?')}: {e}")
                db.session.rollback()
                errors += 1
                continue

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit bike availability batch: {e}")
            return 0

        logger.info(
            f"Bike availability — inserted: {inserted}, "
            f"skipped (duplicate): {skipped}, errors: {errors} "
            f"(out of {len(stations)} stations)"
        )
        return inserted


# ── Weather Scraper ────────────────────────────────────────────────────────────

def scrape_weather(app) -> bool:
    """
    Fetch current Dublin weather from OpenWeather API and insert
    a new record into the weather_current table.

    Skips the insert if a record with the same Unix timestamp already exists.

    Returns:
        bool: True if data was saved successfully, False otherwise
    """
    with app.app_context():
        logger.info("Fetching live weather data from OpenWeather API...")
        data = WeatherService.get_live_weather_data()

        if not data:
            logger.warning("OpenWeather returned no data — skipping weather scrape.")
            return False

        # Check for duplicate by Unix timestamp (primary key)
        dt_unix = data.get("dt")
        if dt_unix:
            exists = (
                db.session.query(WeatherCurrent)
                .filter_by(dt_unix=int(dt_unix))
                .first()
            )
            if exists:
                logger.info(f"Weather record for ts={dt_unix} already exists — skipping.")
                return True  # Not an error, just already saved

        success = WeatherService.save_weather_to_db(data)

        if success:
            city = data.get("name", "Unknown")
            temp = data.get("main", {}).get("temp", "?")
            desc = (data.get("weather") or [{}])[0].get("description", "")
            logger.info(f"Weather saved — {city}: {temp}°C, {desc}")
        else:
            logger.error("WeatherService.save_weather_to_db returned False.")

        return success


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Troithean scraper started")
    logger.info("=" * 60)

    try:
        app = create_app()
    except Exception as e:
        logger.critical(f"Failed to create Flask app: {e}", exc_info=True)
        sys.exit(1)

    bike_count = scrape_bike_availability(app)
    weather_ok = scrape_weather(app)

    logger.info("=" * 60)
    logger.info(
        f"Scraper complete — "
        f"bike records inserted: {bike_count}, "
        f"weather: {'OK' if weather_ok else 'FAILED'}"
    )
    logger.info("=" * 60)

    # Exit with non-zero code if both scrapers failed (useful for cron monitoring)
    if bike_count == 0 and not weather_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

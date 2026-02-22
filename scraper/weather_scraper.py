import os
import requests
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load .env
load_dotenv()

DEBUG = os.getenv("DEBUG", "0") == "1"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY is missing in .env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bike_app")

# Dublin coordinates (you can change these if needed)
LAT = float(os.getenv("WEATHER_LAT", "53.344"))
LON = float(os.getenv("WEATHER_LON", "-6.2672"))


def to_dt_utc(dt_unix: int) -> str:
    """Convert unix seconds -> MySQL DATETIME string in UTC."""
    return datetime.fromtimestamp(dt_unix, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def fetch_current_weather() -> dict:
    """Fetch current weather from OpenWeather."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    resp = requests.get(url, params=params, timeout=20)
    print("HTTP status:", resp.status_code)

    if resp.status_code != 200:
        # Print a short snippet to help debug common issues (401/429/etc.)
        print("Response text:", resp.text[:300])

    resp.raise_for_status()
    return resp.json()


def insert_weather_row(data: dict) -> None:
    """Insert/update a weather snapshot into MySQL."""
    dt_unix = int(data["dt"])
    dt_utc = to_dt_utc(dt_unix)

    main_data = data.get("main") or {}
    wind = data.get("wind") or {}
    clouds = data.get("clouds") or {}
    rain = data.get("rain") or {}
    snow = data.get("snow") or {}
    coord = data.get("coord") or {}
    weather0 = (data.get("weather") or [{}])[0] or {}

    if DEBUG:
        print("DB:", DB_HOST, DB_PORT, DB_NAME)
        print("dt_unix:", dt_unix, "dt_utc:", dt_utc)

    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    cur = conn.cursor()

    sql = """
    INSERT INTO weather_current
    (dt_unix, dt_utc, city_id, city_name, lat, lon,
     temp, feels_like, temp_min, temp_max, pressure, humidity, visibility,
     wind_speed, wind_deg, clouds_all, rain_1h, snow_1h,
     weather_id, weather_main, weather_desc, weather_icon)
    VALUES
    (%s,%s,%s,%s,%s,%s,
     %s,%s,%s,%s,%s,%s,%s,
     %s,%s,%s,%s,%s,
     %s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      dt_utc=VALUES(dt_utc),
      city_id=VALUES(city_id),
      city_name=VALUES(city_name),
      lat=VALUES(lat),
      lon=VALUES(lon),
      temp=VALUES(temp),
      feels_like=VALUES(feels_like),
      temp_min=VALUES(temp_min),
      temp_max=VALUES(temp_max),
      pressure=VALUES(pressure),
      humidity=VALUES(humidity),
      visibility=VALUES(visibility),
      wind_speed=VALUES(wind_speed),
      wind_deg=VALUES(wind_deg),
      clouds_all=VALUES(clouds_all),
      rain_1h=VALUES(rain_1h),
      snow_1h=VALUES(snow_1h),
      weather_id=VALUES(weather_id),
      weather_main=VALUES(weather_main),
      weather_desc=VALUES(weather_desc),
      weather_icon=VALUES(weather_icon);
    """

    params = (
        dt_unix,
        dt_utc,
        data.get("id"),
        data.get("name"),
        coord.get("lat"),
        coord.get("lon"),
        main_data.get("temp"),
        main_data.get("feels_like"),
        main_data.get("temp_min"),
        main_data.get("temp_max"),
        main_data.get("pressure"),
        main_data.get("humidity"),
        data.get("visibility"),
        wind.get("speed"),
        wind.get("deg"),
        clouds.get("all"),
        rain.get("1h"),
        snow.get("1h"),
        weather0.get("id"),
        weather0.get("main"),
        weather0.get("description"),
        weather0.get("icon"),
    )

    cur.execute(sql, params)
    conn.commit()

    cur.close()
    conn.close()


def main():
    print("Fetching weather data...")
    data = fetch_current_weather()
    insert_weather_row(data)
    print("Weather data inserted/updated successfully.")


import time

import time

if __name__ == "__main__":
    total_runs = int(os.getenv("WEATHER_TOTAL_RUNS", "48"))   # 默认跑48次=48小时
    interval = int(os.getenv("WEATHER_INTERVAL_SECONDS", "3600"))

    for i in range(1, total_runs + 1):
        print(f"\n--- Run {i}/{total_runs} ---")
        try:
            main()
        except Exception as e:
            print("Weather scraper error:", repr(e))
        time.sleep(interval)
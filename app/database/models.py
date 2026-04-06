# app/database/models.py
"""
SQLAlchemy ORM models.
All table definitions live here.

Import db from database/db.py — NOT from extensions.py.
"""

from datetime import datetime
from app.database.db import db   # Direct import


#==========================Users===========================================

class User(db.Model):
    __tablename__ = "users"

    id                   = db.Column(db.Integer, primary_key=True)
    first_name           = db.Column(db.String(100), nullable=False)
    last_name            = db.Column(db.String(100), nullable=False)
    email                = db.Column(db.String(255), unique=True, nullable=False)
    phone_number         = db.Column(db.String(20),  nullable=True)
    password_hash        = db.Column(db.String(255), nullable=False)
    email_notifications  = db.Column(db.Boolean, default=False)
    weather_alerts       = db.Column(db.Boolean, default=False)
    prediction_updates   = db.Column(db.Boolean, default=False)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at           = db.Column(db.DateTime, default=datetime.utcnow,
                                     onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "email":        self.email,
            "first_name":   self.first_name,
            "last_name":    self.last_name,
            "phone_number": self.phone_number,
        }


#==========================Stations Table ===================
class Station(db.Model):
    __tablename__ = "station"

    number        = db.Column(db.Integer,     primary_key=True)
    contract_name = db.Column(db.String(64))
    name          = db.Column(db.String(256))
    address       = db.Column(db.String(256))
    banking       = db.Column(db.Boolean)
    bonus         = db.Column(db.Boolean)
    bike_stands   = db.Column(db.Integer)
    position_lat  = db.Column(db.Float)
    position_lng  = db.Column(db.Float)
    status        = db.Column(db.String(32))

    def to_dict(self):
        return {
            "id":       self.number,
            "name":     self.name,
            "address":  self.address,
            "lat":      self.position_lat,
            "lng":      self.position_lng,
            "capacity": self.bike_stands,
            "status":   self.status,
        }


#==========================Availability Table========================

class Availability(db.Model):
    __tablename__ = "availability"

    number                = db.Column(db.Integer,  primary_key=True)
    last_update           = db.Column(db.DateTime, primary_key=True)
    available_bikes       = db.Column(db.Integer)
    available_bike_stands = db.Column(db.Integer)
    status                = db.Column(db.String(32))

    def to_dict(self):
        return {
            "station_id":        self.number,
            "timestamp":         self.last_update.isoformat(),
            "available_bikes":   self.available_bikes,
            "available_stands":  self.available_bike_stands,
            "status":            self.status,
        }


#==========================Weather Table==================================

class WeatherCurrent(db.Model):
    __tablename__ = "weather_current"

    dt_unix       = db.Column(db.Integer,  primary_key=True)
    dt_utc        = db.Column(db.DateTime)
    city_id       = db.Column(db.Integer)
    city_name     = db.Column(db.String(128))
    lat           = db.Column(db.Float)
    lon           = db.Column(db.Float)
    temp          = db.Column(db.Float)
    feels_like    = db.Column(db.Float)
    temp_min      = db.Column(db.Float)
    temp_max      = db.Column(db.Float)
    pressure      = db.Column(db.Integer)
    humidity      = db.Column(db.Integer)
    visibility    = db.Column(db.Integer)
    wind_speed    = db.Column(db.Float)
    wind_deg      = db.Column(db.Integer)
    clouds_all    = db.Column(db.Integer)
    rain_1h       = db.Column(db.Float)
    snow_1h       = db.Column(db.Float)
    weather_id    = db.Column(db.Integer)
    weather_main  = db.Column(db.String(64))
    weather_desc  = db.Column(db.String(128))
    weather_icon  = db.Column(db.String(16))

    def to_dict(self):
        return {
            "temp":        self.temp,
            "feels_like":  self.feels_like,
            "condition":   self.weather_main,
            "humidity":    self.humidity,
            "wind_speed":  self.wind_speed,
        }

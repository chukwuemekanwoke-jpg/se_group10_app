"""
config.py - Flask Application Configuration
Dublin Bikes Web App - COMP30830 Project - Troithean

Centralizes all configuration settings, environment variables,
and constants used throughout the application.
"""

import os
import warnings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class - shared settings."""

    # Flask Settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("Missing required environment variable: SECRET_KEY")

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "dublin_bikes")
    DB_PORT = int(os.getenv("DB_PORT", 3306))

    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    # External API Keys
    JCDECAUX_API_KEY = os.getenv("JCDECAUX_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    for _key, _val in {
        "JCDECAUX_API_KEY":    JCDECAUX_API_KEY,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "GOOGLE_MAPS_API_KEY": GOOGLE_MAPS_API_KEY,
    }.items():
        if not _val:
            warnings.warn(f"Missing API key: {_key}", RuntimeWarning, stacklevel=2)

   
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Log SQL queries during development


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
   

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    SECRET_KEY = "test-secret-key"  # Bypasses RuntimeError in CI
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False


# Export config by environment
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

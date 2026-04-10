"""
config.py - Flask Application Configuration
Dublin Bikes Web App - COMP30830 Project - Troithean

Centralizes all configuration settings, environment variables,
and constants used throughout the application.

Production optimizations for t3.micro instance (1 vCPU, 1GB RAM).
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

    # SQLAlchemy Configuration
    # Optimized for t3.micro with limited memory (1GB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Connection pool
        "pool_size": 3,              # Reduced from default 5 for t3.micro
        "max_overflow": 2,           # Reduced from default 10
        "pool_timeout": 15,          # Fail fast if no connection available
        
        # Connection management
        "pool_pre_ping": True,       # Verify connections are alive before using
        "pool_recycle": 3600,        # Recycle connections every hour
        
        # Disable pool debugging in production
        "echo_pool": False,
    }

    # External API Keys
    JCDECAUX_API_KEY = os.getenv("JCDECAUX_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    # Warn if API keys are missing
    for _key, _val in {
        "JCDECAUX_API_KEY":    JCDECAUX_API_KEY,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "GOOGLE_MAPS_API_KEY": GOOGLE_MAPS_API_KEY,
    }.items():
        if not _val:
            warnings.warn(f"Missing API key: {_key}", RuntimeWarning, stacklevel=2)

    # Session & Security
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
    
    # Use smaller pool for development
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 2,
        "max_overflow": 1,
        "echo_pool": False,
    }


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    # Use optimized pool for production on t3.micro
    # Connection pool is tight but stable
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 3,           # Keep 3 persistent connections
        "max_overflow": 2,        # Allow 2 temp connections
        "pool_timeout": 15,       # Fail fast
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo_pool": False,
    }


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

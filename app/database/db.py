"""
Database instance and session management.
The SQLAlchemy db object is created here once.
Everything else imports from this location.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def _build_database_uri() -> str:
    """
    Reads and validates required DB environment variables.
    Constructs and returns a SQLAlchemy-compatible MySQL URI.
    Raises RuntimeError if any requried variable is missing.
    """
    db_host     = os.getenv("DB_HOST")
    db_user     = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name     = os.getenv("DB_NAME")
    db_port     = int(os.getenv("DB_PORT", 3306))

    required_vars = {
       "DB_HOST":     db_host,
       "DB_USER":     db_user,
       "DB_PASSWORD": db_password,
       "DB_NAME":     db_name,
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            raise RuntimeError(f"Missing required environment variable: {var_name}")

    return (
        f"mysql+mysqlconnector://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )


def init_db(app) -> None:
    """
    Configures the Flask app with the database URI,
    then binds the db instance to the app.
    Called once from create_app().
    """
    # Inject the URI before binding — fail fast if env vars are missing
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", _build_database_uri())
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)

    # Auto-create tables if they don't exist
    with app.app_context():
        from app.database import models  # noqa: F401 — ensures models are registered
        db.create_all()

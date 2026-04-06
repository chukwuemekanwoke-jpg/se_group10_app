"""
Database instance and session management.
The SQLAlchemy db object is created here once.
Everything else imports from this location.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app) -> None:
    """
    Configures the Flask app with the database URI,
    then binds the db instance to the app.
    Called once from create_app().
    """
   
    db.init_app(app)

    # Auto-create tables if they don't exist
    with app.app_context():
        from app.database import models  # noqa: F401 — ensures models are registered
        db.create_all()

"""
Database instance and session management.
The SQLAlchemy db object is created here once.
Everything else imports from this location.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app) -> None:
    """
    Initialize the database with the Flask app.
    
    Configures the Flask app with the database URI,
    then binds the db instance to the app.
    Creates all tables if they don't exist.
    
    Raises:
        RuntimeError: If database initialization fails in production mode.
    
    Called once from create_app().
    """
   
    db.init_app(app)

    # Auto-create tables if they don't exist
    with app.app_context():
        from app.database import models  # noqa: F401 — ensures models are registered
        
        try:
            db.create_all()
            app.logger.info("Database initialized successfully.")
        except Exception as e:
            app.logger.critical(f"Failed to initialize database: {e}")
            
            # In testing mode, allow non-fatal failures
            if app.config.get("TESTING"):
                app.logger.warning("Running in TESTING mode; database error is non-fatal.")
            else:
                # In production, database initialization failure is critical
                raise RuntimeError(f"Database initialization failed: {e}")

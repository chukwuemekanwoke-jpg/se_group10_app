# app/database/__init__.py
from .db import db, init_db
from .models import *  # Expose your SQLAlchemy models

__all__ = ['db', 'init_db']

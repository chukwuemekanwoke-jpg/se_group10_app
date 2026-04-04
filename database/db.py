"""
database/db.py

Database connection setup for the Flask app.
"""

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

required_db_vars = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
    "DB_HOST": DB_HOST
}

for var_name, var_value in required_db_vars.items():
    if not var_value:
        raise RuntimeError(f"Missing required environment variable: {var_name}")

connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    connection_string,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

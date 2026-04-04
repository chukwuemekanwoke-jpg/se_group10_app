import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db():
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_port = int(os.getenv("DB_PORT", 3306))

    required_vars = {
        "DB_HOST": db_host,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            raise RuntimeError(f"Missing required environment variable: {var_name}")

    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )

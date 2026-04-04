from sqlalchemy import text
from werkzeug.security import check_password_hash
from database.db import engine

def authenticate_user(email, password):
    with engine.connect() as connection:
        query = text("""
            SELECT id, first_name, last_name, email, password_hash
            FROM users
            WHERE email = :email
            LIMIT 1
        """)
        result = connection.execute(query, {"email": email}).fetchone()

    if result is None:
        return None

    user = dict(result._mapping)

    if not check_password_hash(user['password_hash'], password):
        return None

    return user

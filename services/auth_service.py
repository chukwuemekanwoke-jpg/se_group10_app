"""
services/auth_service.py

Authentication service functions for:
- looking up users by email
- verifying password hashes
"""

from sqlalchemy import text
from werkzeug.security import check_password_hash


def get_user_by_email(engine, email):
    """
    Fetch a user by email from the users table.
    Returns a dict if found, otherwise None.
    """
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

    return dict(result._mapping)


def authenticate_user(engine, email, password):
    """
    Authenticate a user by email and password.
    Returns the user dict if credentials are valid, otherwise None.
    """
    user = get_user_by_email(engine, email)

    if user is None:
        return None

    if not check_password_hash(user["password_hash"], password):
        return None

    return user

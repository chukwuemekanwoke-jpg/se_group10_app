"""
services/auth_service.py

Authentication service functions for:
- fetching users
- verifying login credentials
- pure business logic, no Flask
- can be tested without the web framework
"""

import logging
from typing import Optional, Dict, Tuple
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates user authentication and registration logic."""

    # Constants for validation
    MIN_PASSWORD_LENGTH = 8
    
    @staticmethod
    def validate_registration_form(
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        confirm_password: str
    ) -> Tuple[bool, str]:
        """
        Validate registration form data.
        
        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email
            password: User's password (plaintext)
            confirm_password: Password confirmation
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check all required fields
        if not all([first_name, last_name, email, password, confirm_password]):
            return False, "Please fill in all required fields."
        
        # Validate email format (basic)
        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address."
        
        # Check password length
        if len(password) < AuthService.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AuthService.MIN_PASSWORD_LENGTH} characters long."
        
        # Check passwords match
        if password != confirm_password:
            return False, "Passwords do not match."
        
        return True, ""

    @staticmethod
    def validate_login_form(email: str, password: str) -> Tuple[bool, str]:
        """
        Validate login form data.
        
        Args:
            email: User's email
            password: User's password (plaintext)
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not email or not password:
            return False, "Please enter both email and password."
        
        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address."
        
        return True, ""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password for storage."""
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password_hash: str, plaintext_password: str) -> bool:
        """Verify a plaintext password against its hash."""
        return check_password_hash(password_hash, plaintext_password)

    @staticmethod
    def authenticate_user(
        email: str,
        password: str,
        user_from_db: Optional[Dict]
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate a user against database credentials.
        
        Args:
            email: User's email
            password: User's plaintext password
            user_from_db: User record from database (None if not found)
        
        Returns:
            Tuple of (success: bool, user_dict: Dict or None)
        """
        # User doesn't exist
        if user_from_db is None:
            return False, None
        
        # Password is wrong
        if not AuthService.verify_password(user_from_db["password_hash"], password):
            return False, None
        
        # Success - return user info (without password hash)
        user_info = {
            "id": user_from_db["id"],
            "email": user_from_db["email"],
            "first_name": user_from_db["first_name"],
            "last_name": user_from_db["last_name"]
        }
        
        return True, user_info


# Test example (doesn't need Flask or database):
if __name__ == "__main__":
    # This works standalone - no imports needed
    form_valid, msg = AuthService.validate_registration_form(
        "John", "Doe", "john@example.com", "securepass123", "securepass123"
    )
    print(f"Valid: {form_valid}, Message: {msg}")
    
    # Hash a password
    hashed = AuthService.hash_password("mypassword")
    print(f"Hashed: {hashed}")
    
    # Verify it
    is_correct = AuthService.verify_password(hashed, "mypassword")
    print(f"Correct: {is_correct}")

from sqlalchemy import text
from werkzeug.security import check_password_hash
from app.database.db import engine


def get_user_by_email(email):
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


def authenticate_user(email, password):
    """
    Authenticate a user by email and password.
    Returns the user dict if credentials are valid, otherwise None.
    """
    user = get_user_by_email(email)

    if user is None:
        return None

    if not check_password_hash(user["password_hash"], password):
        return None

    return user

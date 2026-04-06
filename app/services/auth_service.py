# app/services/auth_service.py
"""
Authentication and user management service.

Pure business logic — no Flask dependencies.
Can be tested without the web framework.
"""

import re
import logging
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

from app.database.db import db
from app.database.models import User

logger = logging.getLogger(__name__)


class AuthService:

    # ── Constants ─────────────────────────────────────────────
    MIN_PASSWORD_LENGTH = 8

    # ── Validation ────────────────────────────────────────────

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using regex.
        Stricter than the original '@' and '.' check.
        """
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message).
        """
        if len(password) < AuthService.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AuthService.MIN_PASSWORD_LENGTH} characters."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number."
        return True, ""

    @staticmethod
    def validate_registration_form(
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        confirm_password: str
    ) -> tuple[bool, str]:
        """
        Validate all registration form fields.
        Returns (is_valid, error_message).
        """
        # Check all required fields are present
        if not all([first_name, last_name, email, password, confirm_password]):
            return False, "Please fill in all required fields."

        # Validate email format
        if not AuthService.validate_email(email):
            return False, "Please enter a valid email address."

        # Validate password strength
        valid, msg = AuthService.validate_password(password)
        if not valid:
            return False, msg

        # Check passwords match
        if password != confirm_password:
            return False, "Passwords do not match."

        return True, ""

    @staticmethod
    def validate_login_form(email: str, password: str) -> tuple[bool, str]:
        """
        Validate login form fields.
        Returns (is_valid, error_message).
        """
        if not email or not password:
            return False, "Please enter both email and password."

        if not AuthService.validate_email(email):
            return False, "Please enter a valid email address."

        return True, ""

    # ── Password Hashing ──────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password for storage."""
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password_hash: str, plaintext_password: str) -> bool:
        """Verify a plaintext password against its hash."""
        return check_password_hash(password_hash, plaintext_password)

    # ── User Queries ──────────────────────────────────────────

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Fetch a user by email using the ORM.
        Returns a User object if found, otherwise None.
        """
        try:
            return db.session.query(User).filter_by(email=email).first()
        except Exception as e:
            logger.error(f"DB error fetching user {email}: {e}")
            return None

    @staticmethod
    def create_user(
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        password: str
    ) -> tuple[bool, str]:
        """
        Register a new user.
        Returns (success, message).
        """
        # Check email is not already registered
        if AuthService.get_user_by_email(email):
            return False, "Email already registered."

        # Validate password strength before hashing
        valid, msg = AuthService.validate_password(password)
        if not valid:
            return False, msg

        try:
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                password_hash=AuthService.hash_password(password),
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {email}")
            return True, "Account created successfully."
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user {email}: {e}")
            return False, "Registration failed. Please try again."

    # ── Authentication ────────────────────────────────────────

    @staticmethod
    def verify_login(email: str, password: str) -> Optional[User]:
        """
        Verify login credentials.
        Returns the User object if valid, otherwise None.
        """
        user = AuthService.get_user_by_email(email)
        if user and AuthService.verify_password(user.password_hash, password):
            logger.info(f"Successful login: {email}")
            return user
        logger.warning(f"Failed login attempt: {email}")
        return None


# ── Standalone Test Block ─────────────────────────────────────
# Runs without Flask or a database — validates pure logic only
if __name__ == "__main__":
    # Test form validation
    valid, msg = AuthService.validate_registration_form(
        "John", "Doe", "john@example.com", "Securepass1", "Securepass1"
    )
    print(f"Registration valid: {valid}, Message: '{msg}'")

    # Test password hashing
    hashed = AuthService.hash_password("Securepass1")
    print(f"Hashed: {hashed}")

    # Test password verification
    print(f"Correct password: {AuthService.verify_password(hashed, 'Securepass1')}")
    print(f"Wrong password:   {AuthService.verify_password(hashed, 'wrongpass')}")

    # Test email validation
    print(f"Valid email:   {AuthService.validate_email('john@example.com')}")
    print(f"Invalid email: {AuthService.validate_email('not-an-email')}")

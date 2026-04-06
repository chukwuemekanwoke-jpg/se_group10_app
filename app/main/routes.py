"""
Main blueprint - frontend routes (pages, authentication forms, etc.)

Responsibilities:
- Handle HTTP requests
- Call services for business logic
- Manage session/cookies
- Render templates
- Return responses

Does NOT:
- Validate forms directly (services do)
- Access database directly (services do)
- Handle passwords (services do)
"""

import secrets
import logging
from flask import (
    render_template, redirect, url_for, flash, session, request, current_app
)
from app.main import main_bp
from app.services.auth_service import AuthService
from app.database.db import get_db  # For user existence check during registration

logger = logging.getLogger(__name__)


# ============ HELPER FUNCTIONS ============

def is_logged_in() -> bool:
    """Check if user is currently logged in."""
    return "user_id" in session


def generate_csrf_token() -> str:
    """Generate and store a CSRF token in session."""
    import secrets
    token = secrets.token_hex(16)
    session["csrf_token"] = token
    return token


def validate_csrf_token(submitted_token: str) -> bool:
    """Verify CSRF token from form submission."""
    stored = session.get("csrf_token")
    return stored and submitted_token and stored == submitted_token


# ============ PUBLIC ROUTES ============

@main_bp.route("/")
def home():
    """Redirect root to index page."""
    return redirect(url_for("main.index_page"))


@main_bp.route("/index")
@main_bp.route("/map")
def index_page():
    """Display the main map page."""
    return render_template(
        "index.html",
        apikey=current_app.config.get("GOOGLE_MAPS_API_KEY"),
        user_name=session.get("user_name"),
        logged_in=is_logged_in()
    )


# ============ AUTHENTICATION: LOGIN ============

@main_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """
    Display login form (GET) or handle login submission (POST).
    """
    if request.method == "POST":
        # 1. VALIDATE CSRF TOKEN
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token. Please try again.", "error")
            return redirect(url_for("main.login_page"))

        # 2. GET AND SANITIZE FORM DATA
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        # 3. VALIDATE FORM (using service)
        is_valid, error_msg = AuthService.validate_login_form(email, password)
        if not is_valid:
            flash(error_msg, "error")
            return render_template(
                "login.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        # 4. FETCH USER FROM DATABASE
        db = None
        cur = None
        try:
            db = get_db()
            cur = db.cursor(dictionary=True)
            
            cur.execute(
                """
                SELECT id, first_name, last_name, email, password_hash
                FROM users WHERE email = %s LIMIT 1
                """,
                (email,)
            )
            user_from_db = cur.fetchone()

        except Exception as e:
            logger.error(f"Database error during login: {e}")
            flash("An internal error occurred. Please try again.", "error")
            return render_template(
                "login.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )
        finally:
            if cur:
                cur.close()
            if db:
                db.close()

        # 5. AUTHENTICATE (using service)
        is_auth, user_info = AuthService.authenticate_user(
            email, password, user_from_db
        )
        
        if not is_auth:
            flash("Invalid email or password.", "error")
            return render_template(
                "login.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        # 6. SET SESSION
        session["user_id"] = user_info["id"]
        session["user_email"] = user_info["email"]
        session["user_name"] = user_info["first_name"]

        flash(f"Welcome back, {user_info['first_name']}!", "success")
        return redirect(url_for("main.index_page"))

    # GET request - just show the form
    return render_template(
        "login.html",
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name")
    )


# ============ AUTHENTICATION: REGISTER ============

@main_bp.route("/register", methods=["GET", "POST"])
def register_page():
    """
    Display registration form (GET) or handle registration (POST).
    """
    if request.method == "POST":
        # 1. VALIDATE CSRF TOKEN
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token. Please try again.", "error")
            return redirect(url_for("main.register_page"))

        # 2. GET AND SANITIZE FORM DATA
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone_number", "").strip() or None
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        # 3. VALIDATE FORM FIELDS INDIVIDUALLY FOR SPECIFIC ERROR MESSAGES
        if not all([first_name, last_name, email, password, confirm]):
            flash("Please fill in all required fields.", "error")
            return render_template(
                "register.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template(
                "register.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template(
                "register.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        # 4. CHECK IF USER ALREADY EXISTS
        db = None
        cur = None
        try:
            db = get_db()
            cur = db.cursor(dictionary=True)

            cur.execute(
                "SELECT id FROM users WHERE email = %s LIMIT 1",
                (email,)
            )
            existing = cur.fetchone()

            if existing:
                flash("An account with this email already exists.", "error")
                return render_template(
                    "register.html",
                    csrf_token=generate_csrf_token(),
                    logged_in=is_logged_in(),
                    user_name=session.get("user_name")
                )

            # 5. HASH PASSWORD AND CREATE USER (using service)
            password_hash = AuthService.hash_password(password)

            cur.execute(
                """
                INSERT INTO users (
                    first_name, last_name, email, phone_number, password_hash,
                    email_notifications, weather_alerts, prediction_updates
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    first_name, last_name, email, phone,
                    password_hash, False, False, False
                )
            )
            db.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("main.login_page"))

        except Exception as e:
            logger.error(f"Registration error: {e}")
            if db:
                db.rollback()
            flash("An internal error occurred. Please try again.", "error")
            return render_template(
                "register.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )
        finally:
            if cur:
                cur.close()
            if db:
                db.close()

    # GET request - just show the form
    return render_template(
        "register.html",
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name")
    )


# ============ USER SETTINGS ============

@main_bp.route("/subscription", methods=["GET", "POST"])
def subscription_page():
    """
    Display subscription preferences (GET) or save them (POST).
    """
    if not is_logged_in():
        flash("Please log in to access this page.", "error")
        return redirect(url_for("main.login_page"))

    db = None
    cur = None

    if request.method == "POST":
        # Validate CSRF
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token.", "error")
            return redirect(url_for("main.subscription_page"))

        # Collect preferences
        email_notifications = 1 if request.form.get("email_notifications") else 0
        weather_alerts = 1 if request.form.get("weather_alerts") else 0
        prediction_updates = 1 if request.form.get("prediction_updates") else 0

        try:
            db = get_db()
            cur = db.cursor()
            
            cur.execute(
                """
                UPDATE users
                SET email_notifications = %s,
                    weather_alerts = %s,
                    prediction_updates = %s
                WHERE id = %s
                """,
                (email_notifications, weather_alerts, prediction_updates, session["user_id"])
            )
            db.commit()
            flash("Preferences saved.", "success")
            return redirect(url_for("main.subscription_page"))

        except Exception as e:
            logger.error(f"Subscription error: {e}")
            if db:
                db.rollback()
            flash("Could not save preferences.", "error")
        finally:
            if cur:
                cur.close()
            if db:
                db.close()

    # GET request - fetch and display current preferences
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        cur.execute(
            """
            SELECT email_notifications, weather_alerts, prediction_updates
            FROM users WHERE id = %s LIMIT 1
            """,
            (session["user_id"],)
        )
        preferences = cur.fetchone() or {}

    except Exception as e:
        logger.error(f"Preference fetch error: {e}")
        preferences = {}
    finally:
        if cur:
            cur.close()
        if db:
            db.close()

    return render_template(
        "subscription.html",
        preferences=preferences,
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name")
    )


# ============ LOGOUT ============

@main_bp.route("/logout")
def logout():
    """Clear user session and redirect to login."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login_page"))

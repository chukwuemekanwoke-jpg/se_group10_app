# app/main/routes.py
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

import logging
from flask import (
    render_template, redirect, url_for, flash, session, request, current_app
)
from app.main import main_bp
from app.services.auth_service import AuthService

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
    return bool(stored and submitted_token and stored == submitted_token)


def render_auth_template(template: str, **kwargs) -> str:
    """
    Render an auth template with common context variables.

    Args:
        template: Template filename
        **kwargs: Additional context variables

    Returns:
        Rendered template string
    """
    return render_template(
        template,
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name"),
        **kwargs
    )


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
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # 3. AUTHENTICATE (fully delegated to service)
        user, error_msg = AuthService.verify_login(email, password)

        if not user:
            flash(error_msg or "Invalid email or password.", "error")
            return render_auth_template("login.html")

        # 4. SET SESSION
        session["user_id"]    = user.id
        session["user_email"] = user.email
        session["user_name"]  = user.first_name

        flash(f"Welcome back, {user.first_name}!", "success")
        return redirect(url_for("main.index_page"))

    # GET request - show the form
    return render_auth_template("login.html")


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
        last_name  = request.form.get("last_name",  "").strip()
        email      = request.form.get("email",      "").strip().lower()
        phone      = request.form.get("phone",      "").strip() or None
        password   = request.form.get("password",   "")
        confirm    = request.form.get("confirm_password", "")

        # 3. BASIC FIELD VALIDATION
        if not all([first_name, last_name, email, password, confirm]):
            flash("Please fill in all required fields.", "error")
            return render_auth_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_auth_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_auth_template("register.html")

        # 4. CREATE USER (fully delegated to service)
        success, message = AuthService.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password=password
        )

        if success:
            flash(message or "Registration successful. Please log in.", "success")
            return redirect(url_for("main.login_page"))

        flash(message or "Registration failed. Please try again.", "error")
        return render_auth_template("register.html")

    # GET request - show the form
    return render_auth_template("register.html")


# ============ USER SETTINGS ============

@main_bp.route("/subscription", methods=["GET", "POST"])
def subscription_page():
    """
    Display subscription preferences (GET) or save them (POST).
    """
    if not is_logged_in():
        flash("Please log in to access this page.", "error")
        return redirect(url_for("main.login_page"))

    if request.method == "POST":
        # 1. VALIDATE CSRF TOKEN
        if not validate_csrf_token(request.form.get("csrf_token", "")):
            flash("Invalid CSRF token.", "error")
            return redirect(url_for("main.subscription_page"))

        # 2. COLLECT PREFERENCES
        preferences = {
            "email_notifications": bool(request.form.get("email_notifications")),
            "weather_alerts":      bool(request.form.get("weather_alerts")),
            "prediction_updates":  bool(request.form.get("prediction_updates"))
        }

        # 3. SAVE PREFERENCES (fully delegated to service)
        success, message = AuthService.update_preferences(
            user_id=session["user_id"],
            preferences=preferences
        )

        flash(message, "success" if success else "error")
        return redirect(url_for("main.subscription_page"))

    # GET request - fetch and display current preferences
    preferences, error = AuthService.get_preferences(session["user_id"])

    if error:
        logger.error(f"Preference fetch error for user {session['user_id']}: {error}")
        flash("Could not load preferences.", "error")

    return render_auth_template(
        "subscription.html",
        preferences=preferences or {}
    )


# ============ LOGOUT ============

@main_bp.route("/logout")
def logout():
    """Clear user session and redirect to login."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login_page"))

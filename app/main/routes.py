import secrets
import logging
from flask import (
    render_template,
    current_app,
    request,
    redirect,
    url_for,
    flash,
    session
)
from werkzeug.security import generate_password_hash, check_password_hash
from . import main_bp
from app.db import get_db

logger = logging.getLogger(__name__)


def generate_csrf_token():
    token = secrets.token_hex(16)
    session["csrf_token"] = token
    return token


def validate_csrf_token(submitted_token):
    stored_token = session.get("csrf_token")
    return stored_token and submitted_token and stored_token == submitted_token


def is_logged_in():
    return "user_id" in session


@main_bp.route("/")
def home():
    return redirect(url_for("main.index_page"))


@main_bp.route("/index")
@main_bp.route("/map")
def index_page():
    return render_template(
        "index.html",
        apikey=current_app.config.get("GOOGLE_MAPS_API_KEY"),
        user_name=session.get("user_name"),
        logged_in=is_logged_in()
    )


@main_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token")
        if not validate_csrf_token(submitted_token):
            flash("Invalid CSRF token. Please try again.", "error")
            return redirect(url_for("main.login_page"))

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template(
                "login.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        db = None
        cur = None

        try:
            db = get_db()
            cur = db.cursor(dictionary=True)

            cur.execute("""
                SELECT id, first_name, last_name, email, phone_number, password_hash
                FROM users
                WHERE email = %s
                LIMIT 1
            """, (email,))
            user = cur.fetchone()

            if not user:
                flash("User not found. Please register first.", "error")
                return redirect(url_for("main.register_page"))

            if not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "error")
                return render_template(
                    "login.html",
                    csrf_token=generate_csrf_token(),
                    logged_in=is_logged_in(),
                    user_name=session.get("user_name")
                )

            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_name"] = user["first_name"]

            flash(f"Welcome back, {user['first_name']}!", "success")
            return redirect(url_for("main.index_page"))

        except Exception as e:
            logger.error("Login error: %s", e)
            flash("An internal error occurred. Please try again later.", "error")
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

    return render_template(
        "login.html",
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name")
    )


@main_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token")
        if not validate_csrf_token(submitted_token):
            flash("Invalid CSRF token. Please try again.", "error")
            return redirect(url_for("main.register_page"))

        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone_number = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not all([first_name, last_name, email, password, confirm_password]):
            flash("Please fill in all required fields.", "error")
            return render_template(
                "register.html",
                csrf_token=generate_csrf_token(),
                logged_in=is_logged_in(),
                user_name=session.get("user_name")
            )

        if password != confirm_password:
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

        db = None
        cur = None

        try:
            db = get_db()
            cur = db.cursor(dictionary=True)

            cur.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email,))
            existing_user = cur.fetchone()

            if existing_user:
                flash("An account with this email already exists.", "error")
                return render_template(
                    "register.html",
                    csrf_token=generate_csrf_token(),
                    logged_in=is_logged_in(),
                    user_name=session.get("user_name")
                )

            password_hash = generate_password_hash(password)

            cur.execute("""
                INSERT INTO users (
                    first_name,
                    last_name,
                    email,
                    phone_number,
                    password_hash,
                    email_notifications,
                    weather_alerts,
                    prediction_updates
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                email,
                phone_number if phone_number else None,
                password_hash,
                False,
                False,
                False
            ))

            db.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("main.login_page"))

        except Exception as e:
            logger.error("Registration error: %s", e)
            flash("An internal error occurred. Please try again later.", "error")
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

    return render_template(
        "register.html",
        csrf_token=generate_csrf_token(),
        logged_in=is_logged_in(),
        user_name=session.get("user_name")
    )


@main_bp.route("/subscription", methods=["GET", "POST"])
def subscription_page():
    if not is_logged_in():
        flash("Please log in to access your subscription settings.", "error")
        return redirect(url_for("main.login_page"))

    db = None
    cur = None

    if request.method == "POST":
        submitted_token = request.form.get("csrf_token")
        if not validate_csrf_token(submitted_token):
            flash("Invalid CSRF token. Please try again.", "error")
            return redirect(url_for("main.subscription_page"))

        email_notifications = 1 if request.form.get("email_notifications") else 0
        weather_alerts = 1 if request.form.get("weather_alerts") else 0
        prediction_updates = 1 if request.form.get("prediction_updates") else 0

        try:
            db = get_db()
            cur = db.cursor()

            cur.execute("""
                UPDATE users
                SET email_notifications = %s,
                    weather_alerts = %s,
                    prediction_updates = %s
                WHERE id = %s
            """, (
                email_notifications,
                weather_alerts,
                prediction_updates,
                session["user_id"]
            ))

            db.commit()

            flash("Subscription preferences saved successfully.", "success")
            return redirect(url_for("main.subscription_page"))

        except Exception as e:
            logger.error("Subscription update error: %s", e)
            flash("Could not save subscription preferences.", "error")
            return redirect(url_for("main.subscription_page"))

        finally:
            if cur:
                cur.close()
            if db:
                db.close()

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            SELECT email_notifications, weather_alerts, prediction_updates
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (session["user_id"],))
        preferences = cur.fetchone()

    except Exception as e:
        logger.error("Subscription fetch error: %s", e)
        preferences = {
            "email_notifications": 0,
            "weather_alerts": 0,
            "prediction_updates": 0
        }

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


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login_page"))

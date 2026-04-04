"""
app.py - Main Flask Application File
Dublin Bikes Web App - COMP30830 Project - Troithean

Main entry point for the Flask app.
Handles:
- Template rendering
- RDS database routes
- Live external API data
- Authentication page routing
- Subscription settings page
- Session-based login/logout
- Placeholder ML prediction
"""

import os
import logging
import requests
from flask import (
    Flask,
    jsonify,
    request,
    abort,
    session,
    redirect,
    url_for,
    render_template,
    flash
)
from sqlalchemy import create_engine, text
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

from services.auth_service import authenticate_user

# Load environment variables from .env
load_dotenv()

# -------------------------------------------------------
# App Setup
# -------------------------------------------------------
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Missing required environment variable: SECRET_KEY")

app.config["SECRET_KEY"] = SECRET_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# RDS Database Configuration
# -------------------------------------------------------
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

# -------------------------------------------------------
# External API Keys
# -------------------------------------------------------
JCDECAUX_API_KEY = os.getenv("JCDECAUX_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# -------------------------------------------------------
# Helper Functions
# -------------------------------------------------------
def get_bike_data():
    """Fetch live Dublin Bikes station data from JCDecaux API."""
    if not JCDECAUX_API_KEY:
        logger.warning("JCDECAUX_API_KEY not set")
        return []

    url = f"https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey={JCDECAUX_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("JCDecaux API Error: %s", e)
        return []


def get_weather():
    """Fetch current Dublin weather from OpenWeather API."""
    if not OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set")
        return {}

    url = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Weather API Error: %s", e)
        return {}


def is_logged_in():
    """Check whether a user is currently logged in."""
    return "user_id" in session


# -------------------------------------------------------
# Frontend Page Routes
# -------------------------------------------------------
@app.route("/")
def root():
    """Render the main homepage/map page."""
    return render_template(
        "index.html",
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
        user_name=session.get("user_name")
    )


@app.route("/login", methods=["GET", "POST"])
def login_page():
    """
    Render login page on GET.
    Handle real login submission on POST using auth_service.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for("login_page"))

        try:
            user = authenticate_user(engine, email, password)

            if user is None:
                flash("Invalid email or password.", "error")
                return redirect(url_for("login_page"))

            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_name"] = user["first_name"]

            flash(f"Welcome back, {user['first_name']}!", "success")
            return redirect(url_for("root"))

        except Exception as e:
            logger.error("Login error: %s", e)
            flash("An internal error occurred. Please try again later.", "error")
            return redirect(url_for("login_page"))

    return render_template("login.html")


@app.route("/subscription", methods=["GET", "POST"])
def subscription_page():
    """
    Render subscription settings page on GET.
    Save subscription preferences to the logged-in user's record on POST.
    """
    if not is_logged_in():
        flash("Please log in to access your subscription settings.", "error")
        return redirect(url_for("login_page"))

    if request.method == "POST":
        email_notifications = bool(request.form.get("email_notifications"))
        weather_alerts = bool(request.form.get("weather_alerts"))
        prediction_updates = bool(request.form.get("prediction_updates"))

        try:
            with engine.begin() as connection:
                query = text("""
                    UPDATE users
                    SET email_notifications = :email_notifications,
                        weather_alerts = :weather_alerts,
                        prediction_updates = :prediction_updates
                    WHERE id = :user_id
                """)
                connection.execute(query, {
                    "email_notifications": email_notifications,
                    "weather_alerts": weather_alerts,
                    "prediction_updates": prediction_updates,
                    "user_id": session["user_id"]
                })

            logger.info(
                "Subscription update saved for user_id=%s: email_notifications=%s, weather_alerts=%s, prediction_updates=%s",
                session["user_id"],
                email_notifications,
                weather_alerts,
                prediction_updates
            )

            flash("Subscription preferences saved successfully.", "success")
            return redirect(url_for("subscription_page"))

        except Exception as e:
            logger.error("Subscription update error: %s", e)
            flash("Could not save subscription preferences.", "error")
            return redirect(url_for("subscription_page"))

    return render_template("subscription.html")


@app.route("/logout")
def logout():
    """Clear the current user session."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("root"))


# -------------------------------------------------------
# Authentication API Routes
# -------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    """Placeholder for user registration logic."""
    return jsonify({"message": "Registration logic placeholder"})


@app.route("/api/login", methods=["POST"])
def login_api():
    """Placeholder for API-based login logic."""
    return jsonify({"message": "Login API placeholder"})


# -------------------------------------------------------
# ML Prediction Route (Placeholder)
# -------------------------------------------------------
@app.route("/api/predict/<int:station_id>")
def predict(station_id):
    """Placeholder for ML model inference."""
    return jsonify({
        "station_id": station_id,
        "predicted_bikes": "ML model logic placeholder"
    })


# -------------------------------------------------------
# RDS API Routes
# -------------------------------------------------------
@app.route("/api/stations")
def get_stations():
    """Fetch all station records from the database."""
    stations = []
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM station;"))
            for row in result:
                stations.append(dict(row._mapping))
        return jsonify(stations=stations)
    except Exception as e:
        logger.error("RDS Fetch Error: %s", e)
        abort(500)


@app.route("/api/availability/<int:station_id>")
def get_availability(station_id):
    """Fetch recent availability history for a station."""
    data = []
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT available_bikes, last_update
                FROM availability
                WHERE number = :id
                ORDER BY last_update DESC
                LIMIT 100
            """)
            result = connection.execute(query, {"id": station_id})

            for row in result:
                data.append(dict(row._mapping))

        if not data:
            abort(404)

        return jsonify(available=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("RDS Query Error: %s", e)
        abort(500)


# -------------------------------------------------------
# Live External API Routes
# -------------------------------------------------------
@app.route("/api/bikes/live")
def live_bikes():
    """Return live bike station data from JCDecaux."""
    return jsonify(get_bike_data())


@app.route("/api/weather")
def live_weather():
    """Return live weather data from OpenWeather."""
    return jsonify(get_weather())


# -------------------------------------------------------
# Error Handlers
# -------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify(error="Resource not found"), 404
    return "Page not found", 404


@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith("/api/"):
        return jsonify(error="Access denied"), 403
    return "Access denied", 403


@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith("/api/"):
        return jsonify(error="Internal server error"), 500
    return "Internal server error", 500


# -------------------------------------------------------
# Run App
# -------------------------------------------------------
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)

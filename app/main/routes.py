from flask import render_template, current_app, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from . import main_bp
from app.db import get_db


@main_bp.route("/")
def home():
    return redirect(url_for("main.login_page"))


@main_bp.route("/index")
@main_bp.route("/map")
def index_page():
    return render_template("index.html", apikey=current_app.config["GOOGLE_MAPS_API_KEY"])


@main_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            SELECT id, first_name, last_name, email, phone_number, password_hash
            FROM users
            WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("User not found. Please register first.", "error")
            return redirect(url_for("main.register_page"))

        if not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        flash("Login successful.", "success")
        return redirect(url_for("main.index_page"))

    return render_template("login.html")


@main_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not all([first_name, last_name, email, phone_number, password, confirm_password]):
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone_number, password_hash)
            VALUES (%s, %s, %s, %s, %s)
        """, (first_name, last_name, email, phone_number, password_hash))

        db.commit()
        cur.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login_page"))

    return render_template("register.html")
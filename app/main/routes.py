from flask import render_template, current_app
from . import main_bp

@main_bp.route("/")
@main_bp.route("/map")
def map_page():
    return render_template("map.html", apikey=current_app.config["GOOGLE_MAPS_API_KEY"])

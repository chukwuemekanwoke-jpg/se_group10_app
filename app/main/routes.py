from . import main_bp

@main_bp.route("/")
def home():
    return "Flask is running"
from . import main_bp

@main_bp.route("/map")
def map_page():
    return "Map page placeholder"

"""
app/api/__init__.py - API Blueprint Package Initialization
Dublin Bikes Web App - COMP30830 Project - Troithean
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

# Import routes to register them with the blueprint
from app.api import routes

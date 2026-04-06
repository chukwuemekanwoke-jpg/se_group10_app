"""
run.py - Flask Application Entry Point
Dublin Bikes Web App - COMP30830 Project - Troithean

Main script to run the Flask development server.
Uses the application factory pattern via create_app().
"""

import os
from app import create_app

# Create the Flask app
# Note: create_app() reads FLASK_ENV from .env automatically
app = create_app()

if __name__ == "__main__":
    # Run the development server
    debug_mode = app.config.get("FLASK_DEBUG", False)
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    app.run(
        host=host,
        port=port,
        debug=debug_mode
    )

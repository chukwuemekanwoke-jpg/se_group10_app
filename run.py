"""
run.py - Flask Application Entry Point
Dublin Bikes Web App - COMP30830 Project - Troithean

Main script to run the Flask development server.
Uses the application factory pattern via create_app().
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Only enable debug if explicitly set
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")  # localhost only in dev
    
    app.run(host=host, port=port, debug=debug, threaded=True)

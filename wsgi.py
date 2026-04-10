"""
wsgi.py - WSGI Entry Point for Production
Dublin Bikes Web App - COMP30830 Project - Troithean

This is the entry point for Gunicorn in production.
DO NOT use this with Flask's development server.

Production launch:
    gunicorn -w 3 -b 0.0.0.0:5000 --timeout 30 wsgi:app

Where:
    -w 3           = 3 worker processes (good for t3.micro with 1 vCPU)
    -b 0.0.0.0:5000 = Bind to port 5000
    --timeout 30   = Kill workers that don't respond in 30s
    wsgi:app       = This file, 'app' variable
"""

import os
from app import create_app

# Create the Flask app using the factory function
app = create_app()

if __name__ == "__main__":
    # This should NOT be called in production
    # Use: gunicorn wsgi:app
    raise RuntimeError(
        "Do not run wsgi.py directly. Use:\n"
        "  gunicorn -w 3 -b 0.0.0.0:5000 --timeout 30 wsgi:app"
    )

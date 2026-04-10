"""
app/middleware.py - Request Middleware and Error Handling
Dublin Bikes Web App - COMP30830 Project - Troithean

Provides:
- Request timing and slow request logging
- Security headers
- Comprehensive error handling
"""

import logging
import time
from flask import request, g, jsonify
import traceback

logger = logging.getLogger(__name__)


def init_middleware(app):
    """
    Initialize middleware for the Flask app.
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Record request start time for performance monitoring."""
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    @app.after_request
    def after_request(response):
        """
        Add response headers and log slow requests.
        """
        elapsed = time.time() - g.start_time
        
        # Log slow requests (over 5 seconds)
        if elapsed > 5:
            logger.warning(
                f"SLOW_REQUEST [id={g.request_id}] "
                f"{request.method} {request.path} "
                f"status={response.status_code} "
                f"elapsed={elapsed:.2f}s"
            )
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Request-ID'] = g.request_id
        
        # Don't expose Flask version
        response.headers.pop('Server', None)
        
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        """Handle 400 Bad Request errors."""
        logger.warning(f"Bad request: {e}")
        return (
            jsonify(error="Bad request", detail=str(e))
            if request.path.startswith("/api/")
            else ("Bad request", 400)
        ), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(e):
        """Handle 401 Unauthorized errors."""
        logger.warning(f"Unauthorized access: {request.path}")
        return (
            jsonify(error="Unauthorized")
            if request.path.startswith("/api/")
            else ("Unauthorized", 401)
        ), 401
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """Handle 403 Forbidden errors."""
        logger.warning(f"Forbidden access: {request.path}")
        return (
            jsonify(error="Access denied")
            if request.path.startswith("/api/")
            else ("Access denied", 403)
        ), 403
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 Not Found errors."""
        logger.debug(f"Resource not found: {request.method} {request.path}")
        return (
            jsonify(error="Resource not found")
            if request.path.startswith("/api/")
            else ("Page not found", 404)
        ), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle 405 Method Not Allowed errors."""
        logger.warning(f"Method not allowed: {request.method} {request.path}")
        return (
            jsonify(error="Method not allowed")
            if request.path.startswith("/api/")
            else ("Method not allowed", 405)
        ), 405
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        """Handle 500 Internal Server errors."""
        logger.error(
            f"Internal server error [id={g.request_id}]: {e}\n"
            f"{traceback.format_exc()}"
        )
        return (
            jsonify(
                error="Internal server error",
                request_id=g.request_id
            )
            if request.path.startswith("/api/")
            else ("Internal server error", 500)
        ), 500
    
    @app.errorhandler(503)
    def handle_service_unavailable(e):
        """Handle 503 Service Unavailable errors."""
        logger.error(f"Service unavailable: {e}")
        return (
            jsonify(error="Service unavailable")
            if request.path.startswith("/api/")
            else ("Service unavailable", 503)
        ), 503
    
    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        """
        Catch-all error handler for unexpected exceptions.
        """
        logger.error(
            f"Unhandled exception [id={g.request_id}]: {type(e).__name__}: {e}\n"
            f"{traceback.format_exc()}",
            exc_info=True
        )
        
        if request.path.startswith("/api/"):
            return jsonify(
                error="Internal server error",
                request_id=g.request_id
            ), 500
        else:
            return "Internal server error", 500

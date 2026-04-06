"""
Flask extensions initialization.
All Flask extensions are created here, then imported elsewhere.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Create extensions WITHOUT binding to an app yet
db = SQLAlchemy()
cors = CORS()

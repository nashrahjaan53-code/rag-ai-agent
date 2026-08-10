import sys
import os

# Ensure the app directory is on the Python path for cPanel Phusion Passenger
sys.path.insert(0, os.path.dirname(__file__))

from a2wsgi import WSGIMiddleware
from main import app

# Expose ASGI FastAPI application as WSGI for cPanel / GoDaddy hosting
application = WSGIMiddleware(app)

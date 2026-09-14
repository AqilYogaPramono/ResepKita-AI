import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import app

try:
    from a2wsgi import WSGIMiddleware
    application = WSGIMiddleware(app)
except ImportError:
    application = app

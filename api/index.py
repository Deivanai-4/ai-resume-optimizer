import os
import sys

# Ensure project root directory is on Python search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Vercel discovers and invokes the WSGI application callable named 'app'
app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

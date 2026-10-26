import os
import sys

# Ensure project root directory is on Python search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


class VercelPathFixMiddleware:
    """
    WSGI middleware to adjust PATH_INFO when running under Vercel functions,
    stripping prefixes like /api/index so Flask handles internal routing properly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        
        # Strip /api/index or /api if Vercel routes into this handler
        if path_info.startswith('/api/index'):
            new_path = path_info[len('/api/index'):]
            environ['PATH_INFO'] = new_path if new_path.startswith('/') else ('/' + new_path)
        elif path_info.startswith('/api'):
            new_path = path_info[len('/api'):]
            environ['PATH_INFO'] = new_path if new_path.startswith('/') else ('/' + new_path)

        if not environ.get('PATH_INFO'):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)


# Vercel discovers and invokes the WSGI application callable named 'app'
app = create_app(os.environ.get('FLASK_CONFIG', 'production'))
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

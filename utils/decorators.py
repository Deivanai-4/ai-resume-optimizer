"""Route decorators — login_required and profile_required."""
from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    """Require user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def profile_required(f):
    """Require user to have basic profile set up."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        # Could add profile completion check here
        return f(*args, **kwargs)
    return decorated_function

"""Reusable helpers for score calculations, file handling, activity logging."""
import os
import re
import uuid
import json
from datetime import datetime
from database.db import execute_db, query_db


def generate_unique_filename(original_name):
    """Generate a unique filename while preserving extension."""
    ext = os.path.splitext(original_name)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_score_badge(score):
    """Return Bootstrap badge class for a score."""
    if score >= 80:
        return 'success'
    elif score >= 60:
        return 'warning'
    else:
        return 'danger'


def get_score_label(score):
    """Return human-readable label for a score."""
    if score >= 85:
        return 'Excellent'
    elif score >= 70:
        return 'Good'
    elif score >= 50:
        return 'Average'
    else:
        return 'Needs Work'


def log_activity(user_id, action, description=None, entity_type=None, entity_id=None):
    """Log a user activity to the activity_logs table."""
    try:
        execute_db(
            '''INSERT INTO activity_logs (user_id, action, description, entity_type, entity_id)
               VALUES (%s,%s,%s,%s,%s)''',
            (user_id, action, description, entity_type, entity_id)
        )
    except Exception:
        pass  # Activity logging should never break the app


def get_recent_activity(user_id, limit=10):
    """Get recent user activity."""
    return query_db(
        'SELECT * FROM activity_logs WHERE user_id=%s ORDER BY created_at DESC LIMIT %s',
        (user_id, limit)
    )


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes / (1024*1024):.1f} MB"


def calculate_profile_score(user_id):
    """Calculate overall career readiness score based on profile data."""
    from models.analysis import AnalysisModel
    averages = AnalysisModel.get_averages(user_id)
    if averages and averages['total_analyses'] > 0:
        return int(averages['avg_career'] or 0)
    return 0


def parse_json_field(value, default=None):
    """Safely parse a JSON field from database."""
    if not value:
        return default if default is not None else []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []

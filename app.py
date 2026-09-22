import os
import json
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for
from config import config
from database.db import init_app as init_db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Explicitly set Flask's secret_key directly from the environment.
    # This is the authoritative assignment — Flask uses app.secret_key (which
    # maps to app.config['SECRET_KEY']) to sign session cookies. An empty or
    # missing value raises RuntimeError on the first session write.
    _secret = os.environ.get('SECRET_KEY') or app.config.get('SECRET_KEY')
    if not _secret:
        raise ValueError(
            "SECRET_KEY environment variable is not set. "
            "Set it in your Render dashboard (or .env for local dev) "
            "before starting the application."
        )
    app.secret_key = _secret
    # Create Upload Folders
    upload_base = app.config["UPLOAD_FOLDER"]
    for folder in ["resumes", "photos", "reports"]:
        os.makedirs(os.path.join(upload_base, folder), exist_ok=True)

    # Initialize Extensions
    bcrypt.init_app(app)
    init_db(app)

    # Import Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.profile import profile_bp
    from routes.resumes import resumes_bp
    from routes.company import company_bp
    from routes.analysis import analysis_bp
    from routes.roadmap import roadmap_bp
    from routes.optimize import optimize_bp
    from routes.interview import interview_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp
    from routes.resume_builder import resume_builder_bp

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(resumes_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(optimize_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(resume_builder_bp)

    # Current User
    @app.context_processor
    def inject_user():
        return {
            "current_user_id": session.get("user_id"),
            "current_user_name": session.get("user_name"),
            "current_user_email": session.get("user_email"),
            "current_user_photo": None,
            "current_profile_completion": session.get("profile_completion", 0),
            "is_logged_in": "user_id" in session,
            "now": datetime.now(),
        }

    # ── Jinja Globals & Filters ─────────────────────────────
    def get_score_label(score):
        score = int(score or 0)
        if score >= 80: return 'Excellent'
        if score >= 60: return 'Good'
        if score >= 40: return 'Average'
        return 'Needs Work'

    def from_json_filter(value):
        if not value: return []
        try:
            return json.loads(value) if isinstance(value, str) else value
        except Exception:
            return []

    app.jinja_env.globals['get_score_label'] = get_score_label
    app.jinja_env.filters['from_json'] = from_json_filter

    # Home Page
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("dashboard.index"))
        return render_template("index.html")


    # Error Pages
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
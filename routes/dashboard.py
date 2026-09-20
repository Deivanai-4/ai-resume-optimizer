"""Dashboard Blueprint."""
from flask import Blueprint, render_template, session
from utils.decorators import login_required
from utils.helpers import log_activity, get_recent_activity, parse_json_field
from models.user import UserModel
from models.profile import ProfileModel
from models.resume import ResumeModel
from models.analysis import AnalysisModel
from models.company import CompanyModel
from database.db import query_db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session.get('user_id')

    user = UserModel.get_by_id(user_id)
    profile = ProfileModel.get(user_id)

    # Stats
    resume_count = ResumeModel.count(user_id)
    averages = AnalysisModel.get_averages(user_id)
    recent_analyses = AnalysisModel.get_recent(user_id, limit=5)
    recent_activity = get_recent_activity(user_id, limit=8)
    latest_resume = ResumeModel.get_latest(user_id)

    # Top companies for discovery
    recommended_companies = CompanyModel.get_all(limit=6)

    # Calculate scores
    avg_ats = int(averages['avg_ats'] or 0) if averages else 0
    avg_skill = int(averages['avg_skill'] or 0) if averages else 0
    avg_career = int(averages['avg_career'] or 0) if averages else 0
    total_analyses = int(averages['total_analyses'] or 0) if averages else 0

    # Skills for display (all skills)
    skills = ProfileModel.get_skills(user_id)

    # Interview stats
    interview_stats = query_db(
        '''SELECT COUNT(*) as total,
                  SUM(CASE WHEN user_answer IS NOT NULL AND user_answer != '' THEN 1 ELSE 0 END) as answered
           FROM interview_questions WHERE user_id=%s''',
        (user_id,), one=True
    ) or {'total': 0, 'answered': 0}
    interview_total = int(interview_stats['total'] or 0)
    interview_answered = int(interview_stats['answered'] or 0)

    # Latest roadmap progress
    latest_roadmap = query_db(
        'SELECT * FROM learning_roadmaps WHERE user_id=%s ORDER BY created_at DESC LIMIT 1',
        (user_id,), one=True
    )
    roadmap_progress = int(latest_roadmap['completion_percent'] or 0) if latest_roadmap else 0

    # Profile completion — always recalculate to stay current
    completion = ProfileModel.calculate_completion(user_id)
    session['profile_completion'] = completion

    return render_template('dashboard.html',
                           user=user,
                           profile=profile,
                           resume_count=resume_count,
                           avg_ats=avg_ats,
                           avg_skill=avg_skill,
                           avg_career=avg_career,
                           total_analyses=total_analyses,
                           recent_analyses=recent_analyses,
                           recent_activity=recent_activity,
                           latest_resume=latest_resume,
                           recommended_companies=recommended_companies,
                           skills=skills,
                           profile_completion=completion,
                           interview_total=interview_total,
                           interview_answered=interview_answered,
                           roadmap_progress=roadmap_progress)

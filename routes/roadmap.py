"""Learning Roadmap Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity, parse_json_field
from models.roadmap import RoadmapModel
from models.analysis import AnalysisModel
from models.company import CompanyModel
from models.resume import ResumeModel
from services.ai_service import generate_learning_roadmap

roadmap_bp = Blueprint('roadmap', __name__)


@roadmap_bp.route('/roadmap')
@login_required
def index():
    user_id = session['user_id']
    
    roadmaps = RoadmapModel.get_all(user_id)
    selected_id = request.args.get('roadmap_id', type=int)
    
    selected_roadmap = None
    items = []
    
    if selected_id:
        selected_roadmap = RoadmapModel.get_by_id(selected_id, user_id)
        if selected_roadmap:
            items = RoadmapModel.get_items(selected_id)
    elif roadmaps:
        selected_roadmap = roadmaps[0]
        items = RoadmapModel.get_items(selected_roadmap['id'])
    
    companies = CompanyModel.get_all(limit=20)
    resumes = ResumeModel.get_all(user_id)
    recent_analyses = AnalysisModel.get_recent(user_id, limit=5)
    
    return render_template('roadmap.html',
                           roadmaps=roadmaps,
                           selected_roadmap=selected_roadmap,
                           items=items,
                           companies=companies,
                           resumes=resumes,
                           recent_analyses=recent_analyses)


@roadmap_bp.route('/roadmap/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    company_id = request.form.get('company_id', type=int)
    resume_id = request.form.get('resume_id', type=int)
    analysis_id = request.form.get('analysis_id', type=int)
    job_title = request.form.get('job_title', '').strip() or 'Software Engineer'
    custom_company_name = request.form.get('custom_company_name', '').strip()
    # Also accept company_name sent directly from the analysis page
    direct_company_name = request.form.get('company_name', '').strip()
    # Comma-separated missing skills sent from the analysis page button
    skills_str = request.form.get('skills', '').strip()

    company = None
    company_name = custom_company_name or direct_company_name or None
    company_skills = []
    missing_skills = []

    # If skills were sent directly from the analysis page, use them
    if skills_str:
        missing_skills = [s.strip() for s in skills_str.split(',') if s.strip()]

    if company_id:
        company = CompanyModel.get_by_id(company_id)
        company_name = company['name'] if company else company_name
        company_skills = CompanyModel.get_required_skills_list(company_id)

    # Pull missing skills from a selected analysis result
    if analysis_id:
        analysis = AnalysisModel.get_by_id(analysis_id, user_id)
        if analysis:
            missing_skills = parse_json_field(analysis.get('missing_skills'))
            if not job_title or job_title == 'Software Engineer':
                job_title = analysis.get('job_title', job_title)
            if not company_name:
                try:
                    import json as _json
                    analysis_data = _json.loads(analysis.get('analysis_data', '{}'))
                    company_name = analysis_data.get('manual_company') or analysis_data.get('company_name')
                except Exception:
                    pass

    # Compute real gap: company required skills minus user's actual profile skills
    from models.profile import ProfileModel
    user_skill_names = [s['skill_name'].lower() for s in ProfileModel.get_skills(user_id)]

    if not missing_skills and company_skills:
        missing_skills = [s for s in company_skills if s.lower() not in user_skill_names]

    # If still no company skills, derive gap from job-title industry standards vs profile
    if not missing_skills:
        title_lower = job_title.lower()
        industry_map = {
            'frontend': ['React', 'HTML', 'CSS', 'JavaScript', 'TypeScript', 'Vue', 'Angular'],
            'backend': ['Python', 'Node.js', 'Django', 'Flask', 'REST API', 'PostgreSQL', 'MySQL'],
            'fullstack': ['React', 'Node.js', 'Python', 'SQL', 'REST API', 'Git', 'Docker'],
            'data': ['Python', 'Pandas', 'NumPy', 'SQL', 'Machine Learning', 'Matplotlib', 'Scikit-learn'],
            'ml': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'NLP', 'Deep Learning', 'SQL'],
            'devops': ['Docker', 'Kubernetes', 'CI/CD', 'Linux', 'AWS', 'Terraform', 'Ansible'],
            'android': ['Java', 'Kotlin', 'Android SDK', 'Jetpack', 'REST API', 'SQLite', 'Git'],
            'software': ['Data Structures', 'Algorithms', 'System Design', 'SQL', 'Git', 'OOP', 'Testing'],
        }
        matched_domain = 'software'
        for key in industry_map:
            if key in title_lower:
                matched_domain = key
                break
        all_for_domain = industry_map[matched_domain]
        missing_skills = [s for s in all_for_domain if s.lower() not in user_skill_names]
        if not missing_skills:
            # User already has everything listed — show growth skills
            missing_skills = ['System Design', 'Docker', 'CI/CD', 'Testing', 'Cloud (AWS/GCP)']

    try:
        roadmap_data = generate_learning_roadmap(missing_skills, job_title, company_name)

        roadmap_id = RoadmapModel.create(
            user_id, company_id, resume_id,
            roadmap_data['title'], roadmap_data['total_weeks']
        )

        for item in roadmap_data['items']:
            RoadmapModel.add_item(
                roadmap_id,
                item['skill_name'], item['priority'], item['duration_weeks'],
                item['order_index'], item.get('resources'), item.get('youtube_links'),
                item.get('doc_links'), item.get('project_ideas')
            )

        log_activity(user_id, 'roadmap_generate',
                     f'Generated learning roadmap: {roadmap_data["title"]}',
                     'roadmap', roadmap_id)
        flash(f'Roadmap generated! {len(roadmap_data["items"])} skills to master. 🗺️', 'success')
        return redirect(url_for('roadmap.index', roadmap_id=roadmap_id))

    except Exception as e:
        flash(f'Failed to generate roadmap. Please try again. ({str(e)[:100]})', 'danger')
        return redirect(url_for('roadmap.index'))


    

@roadmap_bp.route('/roadmap/item/<int:item_id>/update-status', methods=['POST'])
@login_required
def update_item_status(item_id):
    status = request.json.get('status', 'In Progress')
    RoadmapModel.update_item_status(item_id, status)

    from database.db import query_db
    item = query_db('SELECT roadmap_id FROM roadmap_items WHERE id=%s', (item_id,), one=True)
    if item:
        pct = RoadmapModel.update_completion(item['roadmap_id'])
        return jsonify({'success': True, 'completion': pct})
    return jsonify({'success': True})


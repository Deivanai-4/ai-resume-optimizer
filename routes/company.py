"""Company Intelligence Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity
from models.company import CompanyModel
from models.analysis import AnalysisModel
from models.resume import ResumeModel
from models.profile import ProfileModel

company_bp = Blueprint('company', __name__)


@company_bp.route('/company')
@login_required
def index():
    user_id = session['user_id']
    query = request.args.get('q', '').strip()
    if query:
        companies = CompanyModel.search(query)
        log_activity(user_id, 'company_search', f'Searched company: {query}')
    else:
        companies = CompanyModel.get_all(limit=12)
    return render_template('company.html', companies=companies, search_query=query, selected_company=None)


@company_bp.route('/company/<slug>')
@login_required
def detail(slug):
    user_id = session['user_id']
    company = CompanyModel.get_by_slug(slug)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.index'))
    skills = CompanyModel.get_skills(company['id'])
    jobs = CompanyModel.get_jobs(company['id'])
    skills_by_category = {}
    for skill in skills:
        cat = skill['category']
        if cat not in skills_by_category:
            skills_by_category[cat] = []
        skills_by_category[cat].append(skill)
    resumes = ResumeModel.get_all(user_id)
    analyses = AnalysisModel.get_recent(user_id, limit=3)
    company_analyses = [a for a in analyses if a.get('company_id') == company['id']]
    user_skills = [s['skill_name'].lower() for s in ProfileModel.get_skills(user_id)]
    required_skills = CompanyModel.get_required_skills_list(company['id'])
    matched_skills = [s for s in required_skills if s.lower() in user_skills]
    match_percent = int((len(matched_skills) / max(len(required_skills), 1)) * 100)
    log_activity(user_id, 'company_view', f'Viewed company: {company["name"]}', 'company', company['id'])
    return render_template('company.html',
                           companies=CompanyModel.get_all(limit=8),
                           selected_company=company, skills=skills,
                           skills_by_category=skills_by_category, jobs=jobs,
                           resumes=resumes, company_analyses=company_analyses,
                           matched_skills=matched_skills, match_percent=match_percent, search_query='')


@company_bp.route('/company/api/search')
@login_required
def api_search():
    query = request.args.get('q', '').strip()
    companies = CompanyModel.search(query) if query else CompanyModel.get_all(limit=10)
    return jsonify([{'id': c['id'], 'name': c['name'], 'slug': c['slug'],
                     'industry': c['industry'], 'location': c['location']} for c in companies])


@company_bp.route('/company/api/custom', methods=['POST'])
@login_required
def api_custom():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or request.form.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Company name required'}), 400
    log_activity(session['user_id'], 'company_custom', f'Used custom company: {name}')
    return jsonify({'success': True, 'id': None, 'name': name})

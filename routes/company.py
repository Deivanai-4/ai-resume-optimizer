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
    
    ai_profile_data = None
    if company.get('ai_profile'):
        import json
        try:
            ai_profile_data = json.loads(company['ai_profile'])
        except:
            pass
            
    log_activity(user_id, 'company_view', f'Viewed company: {company["name"]}', 'company', company['id'])
    return render_template('company.html',
                           companies=CompanyModel.get_all(limit=8),
                           selected_company=company, skills=skills,
                           skills_by_category=skills_by_category, jobs=jobs,
                           resumes=resumes, company_analyses=company_analyses,
                           matched_skills=matched_skills, match_percent=match_percent, 
                           ai_profile=ai_profile_data, search_query='')

@company_bp.route('/company/<slug>/generate-intelligence', methods=['POST'])
@login_required
def generate_intelligence(slug):
    company = CompanyModel.get_by_slug(slug)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.index'))
        
    from services.ai_service import analyze_company
    from database.db import execute_db
    import json
    
    try:
        profile_data = analyze_company(company['name'], company.get('industry', ''), company.get('description', ''))
        execute_db(
            'UPDATE companies SET ai_profile=%s WHERE id=%s',
            (json.dumps(profile_data), company['id'])
        )
        log_activity(session['user_id'], 'company_intelligence', f'Generated AI Profile for: {company["name"]}')
        flash('AI Company Profile generated successfully!', 'success')
    except Exception as e:
        flash(f'Failed to generate AI profile: {str(e)[:150]}', 'danger')
        
    return redirect(url_for('company.detail', slug=slug, tab='intelligence'))


@company_bp.route('/company/api/search')
@login_required
def api_search():
    query = request.args.get('q', '').strip()
    companies = CompanyModel.search(query) if query else CompanyModel.get_all(limit=10)
    return jsonify([{'id': c['id'], 'name': c['name'], 'slug': c['slug'],
                     'industry': c['industry'], 'location': c['location']} for c in companies])


@company_bp.route('/api/company/search', methods=['POST'])
@login_required
def api_search_post():
    data = request.get_json(silent=True) or {}
    name = (data.get('company_name') or data.get('name') or request.form.get('company_name') or request.form.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Company name required'}), 400
        
    from services.ai_service import ensure_company_profile
    import json
    
    try:
        company = ensure_company_profile(name)
        if company:
            log_activity(session['user_id'], 'company_search_ai', f'Auto-generated/retrieved company: {company["name"]}')
            
            # Extract basic ai_profile if exists
            ai_profile_data = None
            if company.get('ai_profile'):
                try:
                    ai_profile_data = json.loads(company['ai_profile'])
                except:
                    pass
                    
            return jsonify({
                'success': True,
                'company': {
                    'id': company['id'],
                    'name': company['name'],
                    'slug': company['slug'],
                    'industry': company['industry'],
                    'ai_profile': ai_profile_data
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to process company.'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

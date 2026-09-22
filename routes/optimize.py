"""Resume Optimization Blueprint."""
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity, parse_json_field
from models.resume import ResumeModel
from models.company import CompanyModel
from models.analysis import AnalysisModel
from database.db import execute_db, query_db
from services.ai_service import optimize_resume
from services.resume_parser import clean_resume_text

optimize_bp = Blueprint('optimize', __name__)


@optimize_bp.route('/optimize')
@login_required
def index():
    user_id = session['user_id']
    resumes = ResumeModel.get_all(user_id)
    companies = CompanyModel.get_all(limit=20)
    recent_analyses = AnalysisModel.get_recent(user_id, limit=3)
    
    # Load existing optimized resume if selected
    opt_id = request.args.get('opt_id', type=int)
    optimized = None
    if opt_id:
        optimized = query_db(
            'SELECT * FROM optimized_resumes WHERE id=%s AND user_id=%s',
            (opt_id, user_id), one=True
        )
        if optimized:
            optimized['changes_list'] = parse_json_field(optimized.get('changes_made'))
            # Clean up extracted text for display (fixes garbled PDF extraction)
            if optimized.get('original_text'):
                optimized['original_text'] = clean_resume_text(optimized['original_text'])
    
    return render_template('optimize.html',
                           resumes=resumes,
                           companies=companies,
                           recent_analyses=recent_analyses,
                           optimized=optimized)


@optimize_bp.route('/optimize/run', methods=['POST'])
@login_required
def run():
    user_id = session['user_id']
    resume_id = request.form.get('resume_id', type=int)
    company_id = request.form.get('company_id', type=int)
    analysis_id = request.form.get('analysis_id', type=int)
    
    if not resume_id:
        flash('Please select a resume.', 'danger')
        return redirect(url_for('optimize.index'))
    
    resume = ResumeModel.get_by_id(resume_id, user_id)
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('optimize.index'))
    
    company_name = ""
    company_skills = []
    if company_id:
        c = CompanyModel.get_by_id(company_id)
        if c:
            company_name = c['name']
        company_skills = CompanyModel.get_required_skills_list(company_id)
    elif request.form.get('company_id') == 'manual':
        company_name = request.form.get('company_name_manual', '').strip()
    
    # Get job title from form input (it's required now)
    job_title = request.form.get('job_title', '').strip()
    if not job_title:
        flash('Please provide a target job title.', 'danger')
        return redirect(url_for('optimize.index'))
        

    resume_text = resume.get('extracted_text', '') or ''
    
    try:
        result = optimize_resume(resume_text, company_skills, job_title, company_name)
        
        opt_id = execute_db(
            '''INSERT INTO optimized_resumes (user_id, resume_id, analysis_id, original_text,
               optimized_text, professional_summary, changes_made, improvement_score)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, resume_id, analysis_id, resume_text,
             result['optimized_text'], result['professional_summary'],
             json.dumps(result['changes_made']), result['improvement_score']),
            get_id=True
        )
        
        log_activity(user_id, 'resume_optimize',
                     f'Optimized resume {resume["original_name"]} | Score: {result["improvement_score"]}%',
                     'optimize', opt_id)
        flash(f'Resume optimized! Improvement score: {result["improvement_score"]}% ✅', 'success')
        return redirect(url_for('optimize.index', opt_id=opt_id))
    
    except Exception as e:
        flash(f'Optimization failed. Please try again. Error: {str(e)}', 'danger')
        return redirect(url_for('optimize.index'))

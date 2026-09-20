"""AI Analysis Blueprint."""
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity, parse_json_field, get_score_badge, get_score_label
from models.resume import ResumeModel
from models.company import CompanyModel
from models.analysis import AnalysisModel
from models.profile import ProfileModel
from services.ai_service import analyze_resume

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/analysis')
@login_required
def index():
    user_id = session['user_id']
    
    # Pre-selected from query params
    resume_id = request.args.get('resume_id', type=int)
    company_id = request.args.get('company_id', type=int)
    analysis_id = request.args.get('analysis_id', type=int)
    
    resumes = ResumeModel.get_all(user_id)
    companies = CompanyModel.get_all(limit=20)
    recent_analyses = AnalysisModel.get_recent(user_id, limit=5)
    
    selected_analysis = None
    if analysis_id:
        selected_analysis = AnalysisModel.get_by_id(analysis_id, user_id)
        if selected_analysis:
            # Parse JSON fields
            selected_analysis['strengths_list'] = parse_json_field(selected_analysis.get('strengths'))
            selected_analysis['weaknesses_list'] = parse_json_field(selected_analysis.get('weaknesses'))
            selected_analysis['missing_skills_list'] = parse_json_field(selected_analysis.get('missing_skills'))
            selected_analysis['suggestions_list'] = parse_json_field(selected_analysis.get('resume_suggestions'))
            selected_analysis['keywords_list'] = parse_json_field(selected_analysis.get('keyword_analysis'))
            # Populate company_name: try company join first, then manual from ai_data
            if not selected_analysis.get('company_name'):
                if selected_analysis.get('company_id'):
                    c = CompanyModel.get_by_id(selected_analysis['company_id'])
                    selected_analysis['company_name'] = c['name'] if c else ''
                else:
                    try:
                        import json as _j
                        ad = _j.loads(selected_analysis.get('analysis_data') or '{}')
                        selected_analysis['company_name'] = ad.get('manual_company', '')
                    except Exception:
                        selected_analysis['company_name'] = ''
    
    return render_template('analysis.html',
                           resumes=resumes,
                           companies=companies,
                           recent_analyses=recent_analyses,
                           selected_analysis=selected_analysis,
                           preselect_resume=resume_id,
                           preselect_company=company_id,
                           get_score_badge=get_score_badge,
                           get_score_label=get_score_label)


@analysis_bp.route('/analysis/run', methods=['POST'])
@login_required
def run_analysis():
    user_id = session['user_id']
    resume_id = request.form.get('resume_id', type=int)
    company_id = request.form.get('company_id')
    company_manual = request.form.get('company_manual', '').strip()
    job_title = request.form.get('job_title', '').strip() or 'Software Engineer'
    
    # Handle manual company
    if company_id == 'manual':
        company_id = None
    elif company_id:
        try:
            company_id = int(company_id)
        except ValueError:
            company_id = None

    if not resume_id:
        flash('Please select a resume to analyze.', 'danger')
        return redirect(url_for('analysis.index'))
    
    resume = ResumeModel.get_by_id(resume_id, user_id)
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('analysis.index'))
    
    company = None
    company_skills = []
    company_name = company_manual
    if company_id:
        company = CompanyModel.get_by_id(company_id)
        company_skills = CompanyModel.get_required_skills_list(company_id)
        if company:
            company_name = company['name']
        if company and (not job_title or job_title == 'Software Engineer'):
            jobs = CompanyModel.get_jobs(company_id)
            if jobs:
                job_title = jobs[0]['job_title']
    
    # Get user skills
    user_skills = [s['skill_name'] for s in ProfileModel.get_skills(user_id)]
    
    # Run AI analysis
    resume_text = resume.get('extracted_text', '') or ''
    
    try:
        # Pass manual company_name via keyword so ai_service uses it if skills are empty
        result = analyze_resume(resume_text, company_skills, job_title, user_skills, manual_company_name=company_name)
        
        scores = {
            'ats_score': result.get('ats_score', 0),
            'skill_match_score': result.get('skill_match_score', 0),
            'tech_match_score': result.get('tech_match_score', 0),
            'project_match_score': result.get('project_match_score', 0),
            'career_readiness_score': result.get('career_readiness_score', 0),
            'interview_readiness_score': result.get('interview_readiness_score', 0),
            'grammar_score': result.get('grammar_score', 0),
            'formatting_score': result.get('formatting_score', 0),
            'overall_score': result.get('overall_score', 0)
        }
        
        ai_data = {
            'strengths': result.get('strengths', []),
            'weaknesses': result.get('weaknesses', []),
            'missing_skills': result.get('missing_skills', []),
            'suggestions': result.get('suggestions', []),
            'summary': result.get('summary', ''),
            'keywords': result.get('keywords', []),
            'keyword_density': result.get('keyword_density', 0),
            'matched_skills': result.get('matched_skills', []),
            'all_resume_skills': result.get('all_resume_skills', [])
        }
        
        # Save manual company name in ai_data if not linked
        if company_name and not company_id:
            ai_data['manual_company'] = company_name

        analysis_id = AnalysisModel.create(
            user_id, resume_id, company_id, job_title, scores, ai_data
        )
        
        log_activity(user_id, 'analysis_run',
                     f'Analyzed resume against {company_name if company_name else "general"} | Score: {scores["overall_score"]}%',
                     'analysis', analysis_id)
        
        flash(f'Analysis complete! Overall score: {scores["overall_score"]}% ✅', 'success')
        return redirect(url_for('analysis.index', analysis_id=analysis_id))
        
    except Exception as e:
        flash(f'Analysis failed. Please try again. ({str(e)})', 'danger')
        return redirect(url_for('analysis.index'))


@analysis_bp.route('/analysis/<int:analysis_id>/data')
@login_required
def get_analysis_data(analysis_id):
    """Return analysis data as JSON for charts."""
    user_id = session['user_id']
    analysis = AnalysisModel.get_by_id(analysis_id, user_id)
    
    if not analysis:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify({
        'ats_score': analysis['ats_score'],
        'skill_match_score': analysis['skill_match_score'],
        'tech_match_score': analysis['tech_match_score'],
        'project_match_score': analysis['project_match_score'],
        'career_readiness_score': analysis['career_readiness_score'],
        'interview_readiness_score': analysis['interview_readiness_score'],
        'grammar_score': analysis['grammar_score'],
        'formatting_score': analysis['formatting_score'],
        'overall_score': analysis['overall_score'],
        'strengths': parse_json_field(analysis.get('strengths')),
        'weaknesses': parse_json_field(analysis.get('weaknesses')),
        'missing_skills': parse_json_field(analysis.get('missing_skills')),
        'suggestions': parse_json_field(analysis.get('resume_suggestions')),
        'keywords': parse_json_field(analysis.get('keyword_analysis')),
        'summary': analysis.get('resume_summary', '')
    })

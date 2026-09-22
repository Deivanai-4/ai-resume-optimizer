"""Interview Preparation Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity, parse_json_field
from models.company import CompanyModel
from models.resume import ResumeModel
from models.analysis import AnalysisModel
from database.db import execute_db, query_db, execute_many_db
from services.ai_service import generate_interview_questions

interview_bp = Blueprint('interview', __name__)


@interview_bp.route('/interview')
@login_required
def index():
    user_id = session['user_id']
    
    companies = CompanyModel.get_all(limit=20)
    resumes = ResumeModel.get_all(user_id)
    
    # Load existing question set
    session_id = request.args.get('session_id', type=int)
    questions = []
    current_session = None
    
    if session_id:
        current_session = query_db(
            'SELECT * FROM interview_sessions WHERE user_id=%s AND id=%s',
            (user_id, session_id), one=True
        )
        if current_session and current_session.get('session_metadata'):
            import json
            try:
                current_session['metadata'] = json.loads(current_session['session_metadata'])
            except:
                pass
                
        questions = query_db(
            '''SELECT * FROM interview_questions 
               WHERE user_id=%s AND session_id=%s
               ORDER BY category, difficulty, id''',
            (user_id, session_id)
        )
    else:
        # Load most recent session
        latest_session = query_db(
            'SELECT * FROM interview_sessions WHERE user_id=%s ORDER BY created_at DESC LIMIT 1',
            (user_id,), one=True
        )
        if latest_session:
            current_session = latest_session
            if current_session and current_session.get('session_metadata'):
                import json
                try:
                    current_session['metadata'] = json.loads(current_session['session_metadata'])
                except:
                    pass
            questions = query_db(
                'SELECT * FROM interview_questions WHERE user_id=%s AND session_id=%s ORDER BY category, difficulty',
                (user_id, current_session['id'])
            )
            
    # Parse options JSON for template
    for q in questions:
        if q.get('options'):
            import json
            try:
                q['options_list'] = json.loads(q['options'])
            except:
                q['options_list'] = []

    # Stats
    total_questions = query_db(
        'SELECT COUNT(*) as cnt FROM interview_questions WHERE user_id=%s',
        (user_id,), one=True
    )
    
    return render_template('interview.html',
                           companies=companies,
                           resumes=resumes,
                           questions=questions,
                           current_session=current_session,
                           total_questions=total_questions['cnt'] if total_questions else 0)


@interview_bp.route('/interview/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    company_id = request.form.get('company_id', type=int)
    resume_id = request.form.get('resume_id', type=int)
    job_title = request.form.get('job_title', 'Software Engineer').strip()
    difficulty = request.form.get('difficulty', 'All')  # Easy / Medium / Hard / All
    custom_company_name = request.form.get('custom_company_name', '').strip()

    company = None
    company_name = custom_company_name or 'General'
    company_skills = []

    if company_id:
        company = CompanyModel.get_by_id(company_id)
        if company:
            company_name = company['name']
            company_skills = CompanyModel.get_required_skills_list(company_id)
            jobs = CompanyModel.get_jobs(company_id)
            if jobs and (not job_title or job_title == 'Software Engineer'):
                job_title = jobs[0]['job_title']

    resume_text = ''
    if resume_id:
        resume = ResumeModel.get_by_id(resume_id, user_id)
        if resume:
            resume_text = resume.get('extracted_text', '') or ''

    # ── Gather full user context for the AI prompt ────────────────────────
    from models.profile import ProfileModel
    from models.user import UserModel
    user = query_db('SELECT * FROM users WHERE id=%s', (user_id,), one=True)
    user_name = (user.get('full_name') or 'Candidate') if user else 'Candidate'
    user_skills_rows  = ProfileModel.get_skills(user_id)
    user_experience   = ProfileModel.get_experience(user_id)
    user_projects     = ProfileModel.get_projects(user_id)

    user_skills = [s['skill_name'] for s in (user_skills_rows or [])]

    # ── Build seen-question set (text-based, not ID-based) ────────────────
    prev_questions = query_db(
        'SELECT question FROM interview_questions WHERE user_id=%s',
        (user_id,)
    )
    seen_questions = {row['question'].strip().lower() for row in (prev_questions or [])}

    try:
        response = generate_interview_questions(
            job_title=job_title,
            company_name=company_name,
            company_skills=company_skills,
            resume_text=resume_text,
            seen_questions=seen_questions,
            user_name=user_name,
            user_skills=user_skills,
            user_experience=[dict(e) for e in (user_experience or [])],
            user_projects=[dict(p) for p in (user_projects or [])],
            job_description=resume_text[:600],
        )
        
        questions = response.get("questions", [])

        # Filter by difficulty if specified
        if difficulty and difficulty != 'All':
            filtered = [q for q in questions if q.get('diff', 'Medium').lower() == difficulty.lower()]
            questions = filtered if filtered else questions

        import json
        session_metadata = {
            "company": response.get("company", {}),
            "role": response.get("role", {}),
            "recommended_topics": response.get("recommended_topics", [])
        }
        session_id = execute_db(
            '''INSERT INTO interview_sessions (user_id, company_id, resume_id, session_metadata) VALUES (%s,%s,%s,%s)''',
            (user_id, company_id if company_id else None, resume_id if resume_id else None, json.dumps(session_metadata)),
            get_id=True
        )

        args_list = []
        for q in questions:
            options_json = json.dumps(q.get('options', [])) if q.get('options') else None
            correct_answer = q.get('correct_answer', '')
            args_list.append((
                user_id, company_id if company_id else None, resume_id if resume_id else None, session_id, q['q'], '',
                q.get('cat', 'Technical'), q.get('diff', difficulty if difficulty != 'All' else 'Medium'),
                q.get('tip', ''), options_json, correct_answer
            ))
            
        if args_list:
            saved_count = execute_many_db(
                '''INSERT INTO interview_questions (user_id, company_id, resume_id, session_id, question, answer,
                   category, difficulty, ai_tip, options, correct_answer)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                args_list
            )
        else:
            saved_count = 0

        log_activity(user_id, 'interview_generate',
                     f'Generated {saved_count} {difficulty} interview questions for {job_title} at {company_name}')
        flash(f'{saved_count} fresh interview questions generated for {job_title}! 🎯', 'success')
        return redirect(url_for('interview.index', session_id=session_id))

    except Exception as e:
        flash(f'Failed to generate questions. Please try again. Error: {str(e)[:150]}', 'danger')
        return redirect(url_for('interview.index'))



@interview_bp.route('/interview/question/<int:q_id>/answer', methods=['POST'])
@login_required
def save_answer(q_id):
    user_id = session['user_id']
    answer = request.json.get('answer', '')
    execute_db(
        'UPDATE interview_questions SET user_answer=%s WHERE id=%s AND user_id=%s',
        (answer, q_id, user_id)
    )
    return jsonify({'success': True})

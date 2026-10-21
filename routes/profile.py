"""Profile Blueprint — Full profile management with photo upload."""
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from utils.decorators import login_required
from utils.helpers import log_activity, allowed_file, generate_unique_filename
from models.user import UserModel
from models.profile import ProfileModel
from database.db import execute_db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def index():
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id)
    profile = ProfileModel.get(user_id)
    skills = ProfileModel.get_skills(user_id)
    education = ProfileModel.get_education(user_id)
    projects = ProfileModel.get_projects(user_id)
    certifications = ProfileModel.get_certifications(user_id)
    experience = ProfileModel.get_experience(user_id)
    completion = ProfileModel.calculate_completion(user_id)
    from models.resume import ResumeModel
    resumes = ResumeModel.get_all(user_id)
    
    return render_template('profile.html',
                           user=user, profile=profile, skills=skills,
                           education=education, projects=projects,
                           certifications=certifications, experience=experience,
                           profile_completion=completion, resumes=resumes)


@profile_bp.route('/profile/update-basic', methods=['POST'])
@login_required
def update_basic():
    user_id = session['user_id']
    data = {
        'full_name': request.form.get('full_name', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'date_of_birth': request.form.get('date_of_birth') or None,
        'gender': request.form.get('gender') or None,
        'location': request.form.get('location', '').strip(),
        'career_objective': request.form.get('career_objective', '').strip()
    }
    
    if not data['full_name']:
        flash('Full name is required.', 'danger')
        return redirect(url_for('profile.index'))
    
    ProfileModel.update_basic(user_id, data)
    session['user_name'] = data['full_name']
    ProfileModel.calculate_completion(user_id)
    log_activity(user_id, 'profile_update', 'Updated basic profile information')
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile.index') + '#education')


@profile_bp.route('/profile/update-links', methods=['POST'])
@login_required
def update_links():
    user_id = session['user_id']
    github = request.form.get('github_url', '').strip()
    linkedin = request.form.get('linkedin_url', '').strip()
    portfolio = request.form.get('portfolio_url', '').strip()
    
    ProfileModel.update_links(user_id, github, linkedin, portfolio)
    log_activity(user_id, 'profile_update', 'Updated social links')
    flash('Links updated successfully!', 'success')
    return redirect(url_for('profile.index') + '#links')


@profile_bp.route('/profile/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    user_id = session['user_id']
    
    if 'photo' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('profile.index'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('profile.index'))
    
    allowed = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    if not allowed_file(file.filename, allowed):
        flash('Invalid file type. Please upload PNG, JPG, or JPEG.', 'danger')
        return redirect(url_for('profile.index'))
    
    from services.storage_service import upload_profile_photo
    try:
        stored_path = upload_profile_photo(file, user_id)
        ProfileModel.update_photo(user_id, stored_path)
        log_activity(user_id, 'photo_upload', 'Uploaded profile photo')
        flash('Profile photo updated successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Profile photo upload error: {e}")
        flash('Error saving profile photo. Please try again.', 'danger')
    return redirect(url_for('profile.index'))


# --- SKILLS ---
@profile_bp.route('/profile/skills/add', methods=['POST'])
@login_required
def add_skill():
    user_id = session['user_id']
    skill_name = request.form.get('skill_name', '').strip()
    category = request.form.get('category', 'Other')
    proficiency = request.form.get('proficiency', 'Intermediate')
    proficiency_percent = int(request.form.get('proficiency_percent', 50))
    
    if not skill_name:
        flash('Skill name is required.', 'danger')
        return redirect(url_for('profile.index') + '#skills')
    
    ProfileModel.add_skill(user_id, skill_name, category, proficiency, proficiency_percent)
    ProfileModel.calculate_completion(user_id)
    log_activity(user_id, 'skill_add', f'Added skill: {skill_name}')
    flash(f'Skill "{skill_name}" added successfully!', 'success')
    return redirect(url_for('profile.index') + '#projects')


@profile_bp.route('/profile/skills/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    user_id = session['user_id']
    ProfileModel.delete_skill(skill_id, user_id)
    return jsonify({'success': True})


# --- EDUCATION ---
@profile_bp.route('/profile/education/add', methods=['POST'])
@login_required
def add_education():
    user_id = session['user_id']
    data = {
        'degree': request.form.get('degree', '').strip(),
        'field_of_study': request.form.get('field_of_study', '').strip(),
        'institution': request.form.get('institution', '').strip(),
        'university': request.form.get('university', '').strip(),
        'start_year': request.form.get('start_year'),
        'end_year': request.form.get('end_year'),
        'cgpa': request.form.get('cgpa'),
        'percentage': request.form.get('percentage'),
        'is_current': request.form.get('is_current'),
        'description': request.form.get('description', '').strip()
    }
    
    if not data['degree'] or not data['institution']:
        flash('Degree and institution are required.', 'danger')
        return redirect(url_for('profile.index') + '#education')
    
    ProfileModel.add_education(user_id, data)
    ProfileModel.calculate_completion(user_id)
    log_activity(user_id, 'education_add', f'Added education: {data["degree"]} at {data["institution"]}')
    flash('Education added successfully!', 'success')
    return redirect(url_for('profile.index') + '#skills')


@profile_bp.route('/profile/education/delete/<int:edu_id>', methods=['POST'])
@login_required
def delete_education(edu_id):
    user_id = session['user_id']
    ProfileModel.delete_education(edu_id, user_id)
    return jsonify({'success': True})


# --- PROJECTS ---
@profile_bp.route('/profile/projects/add', methods=['POST'])
@login_required
def add_project():
    user_id = session['user_id']
    data = {
        'title': request.form.get('title', '').strip(),
        'description': request.form.get('description', '').strip(),
        'technologies': request.form.get('technologies', '').strip(),
        'github_url': request.form.get('github_url', '').strip(),
        'live_url': request.form.get('live_url', '').strip(),
        'is_current': request.form.get('is_current')
    }
    
    if not data['title']:
        flash('Project title is required.', 'danger')
        return redirect(url_for('profile.index') + '#projects')
    
    ProfileModel.add_project(user_id, data)
    ProfileModel.calculate_completion(user_id)
    log_activity(user_id, 'project_add', f'Added project: {data["title"]}')
    flash(f'Project "{data["title"]}" added successfully!', 'success')
    return redirect(url_for('profile.index') + '#experience')


@profile_bp.route('/profile/projects/delete/<int:proj_id>', methods=['POST'])
@login_required
def delete_project(proj_id):
    user_id = session['user_id']
    ProfileModel.delete_project(proj_id, user_id)
    return jsonify({'success': True})


# --- CERTIFICATIONS ---
@profile_bp.route('/profile/certifications/add', methods=['POST'])
@login_required
def add_certification():
    user_id = session['user_id']
    data = {
        'cert_name': request.form.get('cert_name', '').strip(),
        'issuing_org': request.form.get('issuing_org', '').strip(),
        'issue_date': request.form.get('issue_date') or None,
        'expiry_date': request.form.get('expiry_date') or None,
        'credential_id': request.form.get('credential_id', '').strip(),
        'credential_url': request.form.get('credential_url', '').strip()
    }
    
    if not data['cert_name']:
        flash('Certification name is required.', 'danger')
        return redirect(url_for('profile.index') + '#certifications')
    
    ProfileModel.add_certification(user_id, data)
    log_activity(user_id, 'cert_add', f'Added certification: {data["cert_name"]}')
    flash(f'Certification "{data["cert_name"]}" added successfully!', 'success')
    return redirect(url_for('profile.index') + '#links')


@profile_bp.route('/profile/certifications/delete/<int:cert_id>', methods=['POST'])
@login_required
def delete_certification(cert_id):
    user_id = session['user_id']
    ProfileModel.delete_certification(cert_id, user_id)
    return jsonify({'success': True})


# --- EXPERIENCE ---
@profile_bp.route('/profile/experience/add', methods=['POST'])
@login_required
def add_experience():
    user_id = session['user_id']
    data = {
        'job_title': request.form.get('job_title', '').strip(),
        'company_name': request.form.get('company_name', '').strip(),
        'location': request.form.get('location', '').strip(),
        'start_date': request.form.get('start_date') or None,
        'end_date': request.form.get('end_date') or None,
        'is_current': request.form.get('is_current'),
        'description': request.form.get('description', '').strip()
    }
    
    if not data['job_title'] or not data['company_name']:
        flash('Job title and company name are required.', 'danger')
        return redirect(url_for('profile.index') + '#experience')
    
    ProfileModel.add_experience(user_id, data)
    log_activity(user_id, 'experience_add', f'Added experience: {data["job_title"]} at {data["company_name"]}')
    flash('Experience added successfully!', 'success')
    return redirect(url_for('profile.index') + '#certifications')


@profile_bp.route('/profile/experience/delete/<int:exp_id>', methods=['POST'])
@login_required
def delete_experience(exp_id):
    user_id = session['user_id']
    ProfileModel.delete_experience(exp_id, user_id)
    return jsonify({'success': True})


@profile_bp.route('/profile/upload-extract', methods=['POST'])
@login_required
def upload_extract():
    """Upload a resume file, extract text, parse with LLM (with regex fallback), and update user profile."""
    from services.resume_parser import extract_text, extract_skills_from_text, extract_email, extract_phone, extract_links
    from services.qwen_service import extract_profile_from_resume
    import os
    import uuid
    import re

    user_id = session['user_id']
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['pdf', 'doc', 'docx']:
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload PDF or DOCX'}), 400

    # Save temp file
    from services.storage_service import get_temp_dir
    temp_dir = get_temp_dir()
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
    file.save(temp_path)

    try:
        # Extract raw text
        raw_text = extract_text(temp_path, ext)
        if not raw_text or len(raw_text) < 30:
            return jsonify({'success': False, 'message': 'Could not extract enough text from file'}), 400

        # Try LLM parsing first, fall back to regex if AI is unavailable
        parsed = None
        used_fallback = False
        try:
            parsed = extract_profile_from_resume(raw_text)
        except Exception:
            pass

        if not parsed:
            # --- Regex/heuristic fallback parser ---
            used_fallback = True
            parsed = _parse_resume_with_regex(raw_text)

        # Enforce correct links (override LLM hallucinations like "LinkedIn" or "GitHub")
        regex_links = extract_links(raw_text)
        if 'basic' not in parsed:
            parsed['basic'] = {}
        for key in ['linkedin_url', 'github_url', 'portfolio_url']:
            llm_val = parsed['basic'].get(key, '')
            if not llm_val or '.' not in llm_val or ' ' in llm_val or len(llm_val) < 8:
                parsed['basic'][key] = regex_links.get(key, '')

        # 1. Basic Info
        if parsed.get('basic'):
            ProfileModel.update_basic(user_id, parsed['basic'])

        # 2. Experience – clear first to avoid duplicates
        execute_db('DELETE FROM experience WHERE user_id=%s', (user_id,))
        for exp in parsed.get('experience', []):
            if exp.get('company_name') or exp.get('job_title'):
                end_date = exp.get('end_date', '')
                is_current = str(end_date).lower() in ['present', 'current', 'now', '']
                exp['is_current'] = is_current
                ProfileModel.add_experience(user_id, exp)

        # 3. Education
        execute_db('DELETE FROM education WHERE user_id=%s', (user_id,))
        for edu in parsed.get('education', []):
            if edu.get('institution') or edu.get('degree'):
                ProfileModel.add_education(user_id, edu)

        # 4. Projects
        execute_db('DELETE FROM projects WHERE user_id=%s', (user_id,))
        for proj in parsed.get('projects', []):
            if proj.get('title'):
                ProfileModel.add_project(user_id, proj)

        # 5. Certifications
        execute_db('DELETE FROM certifications WHERE user_id=%s', (user_id,))
        for cert in parsed.get('certifications', []):
            if cert.get('cert_name'):
                ProfileModel.add_certification(user_id, cert)

        # 6. Skills
        execute_db('DELETE FROM skills WHERE user_id=%s', (user_id,))
        for skill in parsed.get('skills', []):
            if skill.get('skill_name'):
                ProfileModel.add_skill(
                    user_id,
                    skill['skill_name'],
                    skill.get('category', 'Other'),
                    skill.get('proficiency', 'Intermediate'),
                    skill.get('proficiency_percent', 50)
                )

        ProfileModel.calculate_completion(user_id)

        msg = 'Profile extracted and saved!'
        if used_fallback:
            msg += ' (AI was unavailable — skills and contact info were extracted via smart matching. You may want to manually complete the other sections.)'

        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _parse_resume_with_regex(text):
    """
    Fallback regex/heuristic parser for when AI is unavailable.
    Extracts skills, email, phone, links and basic name from raw resume text.
    """
    import re
    from services.resume_parser import extract_skills_from_text, extract_email, extract_phone, extract_links

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Name heuristic: first non-email, non-phone line that looks like a name
    name = ''
    for line in lines[:8]:
        if '@' in line or re.search(r'\d{7,}', line):
            continue
        if 2 <= len(line.split()) <= 5 and all(w[0].isupper() for w in line.split() if w):
            name = line
            break

    email = extract_email(text) or ''
    phone = extract_phone(text) or ''
    links = extract_links(text)

    # Extract skills using the existing KNOWN_SKILLS dictionary matcher
    raw_skills = extract_skills_from_text(text)
    skills = [
        {
            'skill_name': s['name'],
            'category': s['category'],
            'proficiency': 'Intermediate',
            'proficiency_percent': 70
        }
        for s in raw_skills
    ]

    # Heuristic: look for education keywords
    education = []
    edu_keywords = ['b.tech', 'b.e.', 'bsc', 'msc', 'm.tech', 'mba', 'bachelor', 'master',
                    'phd', 'diploma', 'engineering', 'university', 'college', 'institute']
    edu_lines = [l for l in lines if any(k in l.lower() for k in edu_keywords)]
    for el in edu_lines[:3]:
        education.append({
            'degree': el,
            'field_of_study': '',
            'institution': el,
            'start_year': '',
            'end_year': '',
            'cgpa': '',
            'description': ''
        })

    # Heuristic: look for experience keywords
    experience = []
    exp_keywords = ['intern', 'engineer', 'developer', 'analyst', 'manager', 'consultant',
                    'software', 'trainee', 'lead', 'architect', 'designer']
    exp_lines = [l for l in lines if any(k in l.lower() for k in exp_keywords)
                 and len(l.split()) >= 2 and len(l) < 100]
    for xl in exp_lines[:5]:
        experience.append({
            'job_title': xl,
            'company_name': '',
            'location': '',
            'start_date': '',
            'end_date': '',
            'is_current': False,
            'description': xl
        })

    return {
        'basic': {
            'full_name': name,
            'email': email,
            'phone': phone,
            'location': '',
            'career_objective': '',
            'linkedin_url': links.get('linkedin_url', ''),
            'github_url': links.get('github_url', ''),
            'portfolio_url': links.get('portfolio_url', '')
        },
        'skills': skills,
        'education': education,
        'experience': experience,
        'projects': [],
        'certifications': []
    }




@profile_bp.route('/profile/api/data')
@login_required
def api_data():
    """Return all profile data as JSON for wizard pre-population and cross-feature data flow."""
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id) or {}
    profile = ProfileModel.get(user_id) or {}
    skills = ProfileModel.get_skills(user_id) or []
    education = ProfileModel.get_education(user_id) or []
    projects = ProfileModel.get_projects(user_id) or []
    certifications = ProfileModel.get_certifications(user_id) or []
    experience = ProfileModel.get_experience(user_id) or []
    completion = ProfileModel.calculate_completion(user_id)

    return jsonify({
        'name': user.get('full_name', ''),
        'email': user.get('email', ''),
        'phone': profile.get('phone', ''),
        'location': profile.get('location', ''),
        'career_objective': profile.get('career_objective', ''),
        'github_url': profile.get('github_url', ''),
        'linkedin_url': profile.get('linkedin_url', ''),
        'portfolio_url': profile.get('portfolio_url', ''),
        'profile_completion': completion,
        'skills': [{'name': s.get('skill_name', ''), 'category': s.get('category', ''),
                    'proficiency': s.get('proficiency', 'Intermediate'),
                    'percent': s.get('proficiency_percent', 50)} for s in skills],
        'education': [{'degree': e.get('degree', ''), 'field': e.get('field_of_study', ''),
                       'institution': e.get('institution', ''), 'university': e.get('university', ''),
                       'start_year': str(e.get('start_year', '') or ''),
                       'end_year': str(e.get('end_year', '') or ''),
                       'cgpa': str(e.get('cgpa', '') or ''),
                       'is_current': bool(e.get('is_current'))} for e in education],
        'projects': [{'title': p.get('title', ''), 'description': p.get('description', ''),
                      'technologies': p.get('technologies', ''), 'github_url': p.get('github_url', ''),
                      'live_url': p.get('live_url', '')} for p in projects],
        'certifications': [{'name': c.get('cert_name', ''), 'org': c.get('issuing_org', ''),
                            'date': str(c.get('issue_date', '') or '')} for c in certifications],
        'experience': [{'title': ex.get('job_title', ''), 'company': ex.get('company_name', ''),
                        'location': ex.get('location', ''), 'description': ex.get('description', ''),
                        'start_date': str(ex.get('start_date', '') or ''),
                        'end_date': str(ex.get('end_date', '') or ''),
                        'is_current': bool(ex.get('is_current'))} for ex in experience],
    })


@profile_bp.route('/profile/api/extract-resume', methods=['POST'])
@login_required
def api_extract_resume():
    """Extract data from uploaded resume or existing resume ID without saving."""
    from services.resume_parser import extract_text, extract_links
    from services.qwen_service import extract_profile_from_resume
    import os
    import uuid
    from models.resume import ResumeModel
    from flask import current_app

    user_id = session['user_id']
    raw_text = None
    
    # Check if a resume_id was provided
    resume_id = request.form.get('resume_id') or (request.json.get('resume_id') if request.is_json else None)
    if resume_id:
        resume = ResumeModel.get_by_id(resume_id, user_id)
        if not resume:
            return jsonify({'success': False, 'message': 'Resume not found'}), 404
        raw_text = resume.get('extracted_text')
        
        # If it doesn't have extracted text, we might need to parse the file
        if not raw_text:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume.get('file_path', ''))
            ext = resume.get('file_type', 'pdf')
            if os.path.exists(file_path):
                raw_text = extract_text(file_path, ext)
    else:
        # Check if a file was uploaded
        if 'resume' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded or resume selected'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
            
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ['pdf', 'doc', 'docx']:
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload PDF or DOCX'}), 400
            
        from services.storage_service import get_temp_dir
        temp_dir = get_temp_dir()
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
        file.save(temp_path)
        
        try:
            raw_text = extract_text(temp_path, ext)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not raw_text or len(raw_text) < 30:
        return jsonify({'success': False, 'message': 'Could not extract enough text from file'}), 400

    # Try LLM parsing first, fall back to regex
    parsed = None
    used_fallback = False
    try:
        parsed = extract_profile_from_resume(raw_text)
    except Exception:
        pass

    if not parsed:
        used_fallback = True
        parsed = _parse_resume_with_regex(raw_text)
        
    # Enforce correct links (override LLM hallucinations like "LinkedIn" or "GitHub")
    regex_links = extract_links(raw_text)
    if 'basic' not in parsed:
        parsed['basic'] = {}
    for key in ['linkedin_url', 'github_url', 'portfolio_url']:
        llm_val = parsed['basic'].get(key, '')
        if not llm_val or '.' not in llm_val or ' ' in llm_val or len(llm_val) < 8:
            parsed['basic'][key] = regex_links.get(key, '')
        
    return jsonify({
        'success': True, 
        'data': parsed, 
        'used_fallback': used_fallback
    })

@profile_bp.route('/profile/api/save-imported-data', methods=['POST'])
@login_required
def save_imported_data():
    """Save selected fields from the extracted resume to the profile."""
    user_id = session['user_id']
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
        
    try:
        # Basic Info
        basic = data.get('basic', {})
        if basic:
            current_user = UserModel.get_by_id(user_id) or {}
            current_profile = ProfileModel.get(user_id) or {}
            
            merged_basic = {
                'full_name': basic.get('full_name') or current_user.get('full_name', ''),
                'phone': basic.get('phone') or current_profile.get('phone', ''),
                'location': basic.get('location') or current_profile.get('location', ''),
                'date_of_birth': basic.get('date_of_birth') or current_profile.get('date_of_birth'),
                'gender': current_profile.get('gender'),
                'career_objective': basic.get('career_objective') or current_profile.get('career_objective', '')
            }
            
            # Ensure row exists or update it
            execute_db(
                '''INSERT INTO student_profiles (user_id, phone, date_of_birth, gender, location, career_objective, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, NOW())
                   ON DUPLICATE KEY UPDATE
                   phone=VALUES(phone), date_of_birth=VALUES(date_of_birth), gender=VALUES(gender),
                   location=VALUES(location), career_objective=VALUES(career_objective), updated_at=NOW()''',
                (user_id, merged_basic.get('phone'), merged_basic.get('date_of_birth') or None,
                 merged_basic.get('gender'), merged_basic.get('location'), merged_basic.get('career_objective'))
            )
            
            execute_db('UPDATE users SET full_name=%s WHERE id=%s', (merged_basic.get('full_name'), user_id))
            if basic.get('full_name'):
                session['user_name'] = merged_basic.get('full_name')

            # Update links using ON DUPLICATE KEY
            new_github = basic.get('github_url') or current_profile.get('github_url', '')
            new_linkedin = basic.get('linkedin_url') or current_profile.get('linkedin_url', '')
            new_portfolio = basic.get('portfolio_url') or current_profile.get('portfolio_url', '')
            
            execute_db(
                '''INSERT INTO student_profiles (user_id, github_url, linkedin_url, portfolio_url)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   github_url=VALUES(github_url), linkedin_url=VALUES(linkedin_url), portfolio_url=VALUES(portfolio_url)''',
                (user_id, new_github, new_linkedin, new_portfolio)
            )
            
        # Experience
        existing_exp = ProfileModel.get_experience(user_id) or []
        for exp in data.get('experience', []):
            if isinstance(exp, str):
                continue
            if exp.get('company_name') or exp.get('job_title'):
                if not any(e['company_name'] == exp.get('company_name') and e['job_title'] == exp.get('job_title') for e in existing_exp):
                    end_date = exp.get('end_date', '')
                    is_current = str(end_date).lower() in ['present', 'current', 'now', '']
                    exp['is_current'] = is_current
                    ProfileModel.add_experience(user_id, exp)
                
        # Education
        existing_edu = ProfileModel.get_education(user_id) or []
        for edu in data.get('education', []):
            if isinstance(edu, str):
                continue
            if edu.get('institution') or edu.get('degree'):
                if not any(e['institution'] == edu.get('institution') and e['degree'] == edu.get('degree') for e in existing_edu):
                    ProfileModel.add_education(user_id, edu)
                
        # Projects
        existing_proj = ProfileModel.get_projects(user_id) or []
        for proj in data.get('projects', []):
            if isinstance(proj, str):
                proj = {'title': proj}
            if proj.get('title'):
                if not any(p['title'] == proj.get('title') for p in existing_proj):
                    ProfileModel.add_project(user_id, proj)
                
        # Certifications
        existing_cert = ProfileModel.get_certifications(user_id) or []
        for cert in data.get('certifications', []):
            if isinstance(cert, str):
                cert = {'cert_name': cert}
            if cert.get('cert_name'):
                if not any(c['cert_name'] == cert.get('cert_name') for c in existing_cert):
                    ProfileModel.add_certification(user_id, cert)
                
        # Skills
        existing_skills = ProfileModel.get_skills(user_id) or []
        for skill in data.get('skills', []):
            if isinstance(skill, str):
                skill = {'skill_name': skill, 'category': 'Other'}
            if skill.get('skill_name'):
                if not any(s['skill_name'].lower() == skill.get('skill_name').lower() for s in existing_skills):
                    ProfileModel.add_skill(
                        user_id,
                        skill['skill_name'],
                        skill.get('category', 'Other'),
                        skill.get('proficiency', 'Intermediate'),
                        skill.get('proficiency_percent', 50)
                    )
                
        ProfileModel.calculate_completion(user_id)
        log_activity(user_id, 'profile_import', 'Imported data from resume')
        
        return jsonify({'success': True, 'message': 'Imported data saved successfully'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error saving data: {str(e)}'}), 500

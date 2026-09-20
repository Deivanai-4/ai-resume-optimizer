"""Resumes Blueprint — Upload, list, delete, parse, preview."""
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app, send_file
from utils.decorators import login_required
from utils.helpers import log_activity, allowed_file, generate_unique_filename, format_file_size
from models.resume import ResumeModel
from models.profile import ProfileModel
from models.generated_resume import GeneratedResumeModel
from services.resume_parser import parse_resume

resumes_bp = Blueprint('resumes', __name__)


@resumes_bp.route('/resumes')
@login_required
def index():
    user_id = session['user_id']
    resumes = ResumeModel.get_all(user_id)
    gen_resumes = GeneratedResumeModel.get_all(user_id)
    return render_template('resumes.html', resumes=resumes, gen_resumes=gen_resumes)


@resumes_bp.route('/resumes/upload', methods=['POST'])
@login_required
def upload():
    user_id = session['user_id']
    is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if 'resume_file' not in request.files:
        if is_ajax: return jsonify({'success': False, 'message': 'No file selected.'})
        flash('No file selected.', 'danger')
        return redirect(url_for('resumes.index'))
    
    file = request.files['resume_file']
    if file.filename == '':
        if is_ajax: return jsonify({'success': False, 'message': 'No file selected.'})
        flash('No file selected.', 'danger')
        return redirect(url_for('resumes.index'))
    
    allowed = current_app.config['ALLOWED_RESUME_EXTENSIONS']
    if not allowed_file(file.filename, allowed):
        if is_ajax: return jsonify({'success': False, 'message': 'Invalid file type. Only PDF and DOCX files are supported.'})
        flash('Invalid file type. Only PDF and DOCX files are supported.', 'danger')
        return redirect(url_for('resumes.index'))
    
    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > current_app.config['MAX_CONTENT_LENGTH']:
        if is_ajax: return jsonify({'success': False, 'message': 'File too large. Maximum size is 5MB.'})
        flash('File too large. Maximum size is 5MB.', 'danger')
        return redirect(url_for('resumes.index'))
    
    resumes_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', str(user_id))
    os.makedirs(resumes_dir, exist_ok=True)
    
    original_name = file.filename
    file_type = original_name.rsplit('.', 1)[1].lower()
    filename = generate_unique_filename(original_name)
    file_path = os.path.join(resumes_dir, filename)
    file.save(file_path)
    
    resume_id = ResumeModel.create(
        user_id, filename, original_name, file_path, file_size, file_type
    )
    
    # Parse immediately
    try:
        parsed = parse_resume(file_path, file_type)
        skill_names = [s['name'] for s in parsed['skills']]
        ResumeModel.update_parsed_data(resume_id, parsed['text'], skill_names)
        
        # Auto-add new skills to profile
        existing_skills = [s['skill_name'].lower() for s in ProfileModel.get_skills(user_id)]
        for skill in parsed['skills']:
            if skill['name'].lower() not in existing_skills:
                ProfileModel.add_skill(user_id, skill['name'], skill['category'], 'Intermediate', 50)
        
        ProfileModel.calculate_completion(user_id)
        log_activity(user_id, 'resume_upload', f'Uploaded resume: {original_name} | {len(skill_names)} skills extracted')
        if is_ajax:
            return jsonify({'success': True, 'message': f'Resume uploaded successfully! {len(skill_names)} skills extracted. ✅'})
        flash(f'Resume uploaded successfully! {len(skill_names)} skills extracted. ✅', 'success')
    except Exception as e:
        current_app.logger.error(f"Parse error: {e}")
        log_activity(user_id, 'resume_upload', f'Uploaded resume: {original_name} (parse failed)')
        if is_ajax:
            return jsonify({'success': True, 'message': 'Resume uploaded successfully! (Parsing failed — you can retry later)'})
        flash('Resume uploaded successfully! (Parsing failed — you can retry later)', 'warning')
    
    return redirect(url_for('resumes.index'))


@resumes_bp.route('/resumes/delete/<int:resume_id>', methods=['POST'])
@login_required
def delete(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    
    if not resume:
        return jsonify({'success': False, 'message': 'Resume not found'}), 404
    
    # Delete file
    try:
        if os.path.exists(resume['file_path']):
            os.remove(resume['file_path'])
    except Exception:
        pass
    
    ResumeModel.delete(resume_id, user_id)
    log_activity(user_id, 'resume_delete', f'Deleted resume: {resume["original_name"]}')
    
    if request.is_json:
        return jsonify({'success': True})
    flash('Resume deleted successfully.', 'success')
    return redirect(url_for('resumes.index'))


@resumes_bp.route('/resumes/download/<int:resume_id>')
@login_required
def download(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.index'))
    
    if not os.path.exists(resume['file_path']):
        flash('Resume file not found on server.', 'danger')
        return redirect(url_for('resumes.index'))
    
    return send_file(resume['file_path'], 
                     download_name=resume['original_name'],
                     as_attachment=True)


@resumes_bp.route('/resumes/<int:resume_id>/parse', methods=['POST'])
@login_required
def parse(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.index'))
    try:
        parsed = parse_resume(resume['file_path'], resume['file_type'])
        skill_names = [s['name'] for s in parsed['skills']]
        ResumeModel.update_parsed_data(resume_id, parsed['text'], skill_names)
        flash(f'Resume re-parsed! {len(skill_names)} skills found.', 'success')
    except Exception as e:
        current_app.logger.error(f"Re-parse error: {e}")
        flash('Re-parse failed. File may be missing or corrupt.', 'danger')
    return redirect(url_for('resumes.index'))


@resumes_bp.route('/resumes/<int:resume_id>/details')
@login_required
def details(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.index'))
    
    import json
    skills = []
    if resume.get('extracted_skills'):
        try:
            skills = json.loads(resume['extracted_skills'])
        except Exception:
            skills = []
    
    return jsonify({
        'id': resume['id'],
        'name': resume['original_name'],
        'size': format_file_size(resume.get('file_size', 0)),
        'type': resume['file_type'].upper(),
        'uploaded': str(resume['upload_date']),
        'is_parsed': bool(resume['is_parsed']),
        'skills': skills,
        'word_count': len(resume['extracted_text'].split()) if resume.get('extracted_text') else 0
    })

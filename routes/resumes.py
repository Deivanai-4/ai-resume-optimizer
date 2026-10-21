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
    
    original_name = file.filename
    file_type = original_name.rsplit('.', 1)[1].lower()
    filename = generate_unique_filename(original_name)

    from services.storage_service import (
        get_temp_dir, upload_resume_file, get_private_download_url,
        is_cloudinary_id, delete_stored_file, fetch_resume_for_processing
    )

    # Save to writable temp directory first for parsing
    temp_dir = get_temp_dir()
    temp_path = os.path.join(temp_dir, filename)
    file.save(temp_path)

    # Upload to persistent storage (Cloudinary private raw asset or local folder)
    try:
        stored_path = upload_resume_file(temp_path, user_id, original_name)
    except Exception as e:
        current_app.logger.error(f"Failed to upload resume to persistent storage: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if is_ajax: return jsonify({'success': False, 'message': 'Storage error. Please try again.'})
        flash('Storage error while saving resume. Please check configuration.', 'danger')
        return redirect(url_for('resumes.index'))

    resume_id = ResumeModel.create(
        user_id, filename, original_name, stored_path, file_size, file_type
    )

    # Parse resume text and skills from the local temp file
    try:
        parsed = parse_resume(temp_path, file_type)
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
    finally:
        # Clean up temp file if stored in cloud
        if is_cloudinary_id(stored_path) and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
    
    return redirect(url_for('resumes.index'))


@resumes_bp.route('/resumes/delete/<int:resume_id>', methods=['POST'])
@login_required
def delete(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    
    if not resume:
        return jsonify({'success': False, 'message': 'Resume not found'}), 404
    
    # Delete file from Cloudinary or local disk
    from services.storage_service import delete_stored_file
    delete_stored_file(resume['file_path'], resource_type='raw', is_private=True)
    
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

    from services.storage_service import is_cloudinary_id, get_private_download_url
    path = resume['file_path']

    if is_cloudinary_id(path):
        try:
            url = get_private_download_url(path, resume['file_type'])
            return redirect(url)
        except Exception as e:
            current_app.logger.error(f"Failed to generate download URL: {e}")
            flash('Error generating secure download link.', 'danger')
            return redirect(url_for('resumes.index'))
    else:
        # Local file fallback
        if os.path.exists(path):
            return send_file(path, 
                             download_name=resume['original_name'],
                             as_attachment=True)
        flash('This resume was stored on a previous server and is no longer available for download.', 'warning')
        return redirect(url_for('resumes.index'))


@resumes_bp.route('/resumes/<int:resume_id>/parse', methods=['POST'])
@login_required
def parse(resume_id):
    user_id = session['user_id']
    resume = ResumeModel.get_by_id(resume_id, user_id)
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.index'))
    
    from services.storage_service import fetch_resume_for_processing
    local_path = None
    is_temp = False
    try:
        local_path, is_temp = fetch_resume_for_processing(resume['file_path'], resume['file_type'])
        parsed = parse_resume(local_path, resume['file_type'])
        skill_names = [s['name'] for s in parsed['skills']]
        ResumeModel.update_parsed_data(resume_id, parsed['text'], skill_names)
        flash(f'Resume re-parsed! {len(skill_names)} skills found.', 'success')
    except Exception as e:
        current_app.logger.error(f"Re-parse error: {e}")
        flash('Re-parse failed. File may be missing or corrupt.', 'danger')
    finally:
        if is_temp and local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except OSError:
                pass
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

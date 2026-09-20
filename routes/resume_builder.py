"""
AI Resume Builder Blueprint
============================
Routes:
  GET  /resume/create                  — wizard entry (Flow A / B chooser)
  POST /resume/generate                — trigger AI generation, save, redirect to preview
  GET  /resume/preview/<id>            — full preview + ATS panel
  POST /resume/edit/<id>               — save manual edits
  POST /resume/regenerate-section/<id> — AJAX: regenerate one section
  POST /resume/change-template/<id>    — AJAX: switch template
  GET  /resume/download/pdf/<id>       — serve PDF
  GET  /resume/download/docx/<id>      — serve DOCX
  POST /resume/delete/<id>             — soft-delete
"""
import json
import logging
import os

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, jsonify, current_app, send_file)
from utils.decorators import login_required
from utils.helpers import log_activity, allowed_file
from models.resume import ResumeModel
from models.company import CompanyModel
from models.generated_resume import GeneratedResumeModel

logger = logging.getLogger(__name__)

resume_builder_bp = Blueprint('resume_builder', __name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _gen_dir(user_id):
    """Return (and create) the generated-resumes directory for this user."""
    base = os.path.join(current_app.config['UPLOAD_FOLDER'], 'generated', str(user_id))
    os.makedirs(base, exist_ok=True)
    return base


# ---------------------------------------------------------------------------
# GET /resume/create  — wizard entry
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/create')
@login_required
def create():
    user_id = session['user_id']
    resumes = ResumeModel.get_all(user_id)
    companies = CompanyModel.get_all(limit=50)

    # Fetch profile data for wizard pre-fill and target role auto-populate
    from models.profile import ProfileModel
    from models.user import UserModel
    user = UserModel.get_by_id(user_id) or {}
    profile = ProfileModel.get(user_id) or {}
    skills = ProfileModel.get_skills(user_id) or []
    education = ProfileModel.get_education(user_id) or []
    projects = ProfileModel.get_projects(user_id) or []
    experience = ProfileModel.get_experience(user_id) or []
    certifications = ProfileModel.get_certifications(user_id) or []

    return render_template('resume_builder.html',
                           resumes=resumes,
                           companies=companies,
                           user=user,
                           profile=profile,
                           skills=skills,
                           education=education,
                           projects=projects,
                           experience=experience,
                           certifications=certifications)


# ---------------------------------------------------------------------------
# POST /resume/generate  — trigger AI generation
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/generate', methods=['POST'])
@login_required
def generate():
    user_id   = session['user_id']
    form      = request.form

    # ── Input collection ─────────────────────────────────────────────────────
    source_resume_id  = form.get('source_resume_id', type=int)
    company_id        = form.get('company_id', type=int) or None
    company_name_man  = form.get('company_name_manual', '').strip()
    job_role          = form.get('job_role', 'Software Engineer').strip() or 'Software Engineer'
    job_description   = form.get('job_description', '').strip()
    template          = form.get('template', 'classic')
    if template not in ('classic', 'modern', 'minimal'):
        template = 'classic'

    # ── Wizard data (Flow B — no resume) ────────────────────────────────────
    wizard_raw = form.get('wizard_data', '')
    wizard_data = None
    if wizard_raw:
        try:
            wizard_data = json.loads(wizard_raw)
        except (json.JSONDecodeError, TypeError):
            wizard_data = None

    # ── Source resume text (Flow A) ──────────────────────────────────────────
    source_resume_text = None
    if source_resume_id:
        resume = ResumeModel.get_by_id(source_resume_id, user_id)
        if resume:
            source_resume_text = resume.get('extracted_text', '') or ''

    company_name_display = company_name_man
    if company_id and not company_name_display:
        c = CompanyModel.get_by_id(company_id)
        if c:
            company_name_display = c['name']

    if not company_name_display:
        company_name_display = 'General'

    # ── Run AI generation ────────────────────────────────────────────────────
    try:
        from services.resume_generation_service import generate_resume
        result = generate_resume(
            user_id             = user_id,
            wizard_data         = wizard_data,
            source_resume_id    = source_resume_id,
            company_id          = company_id,
            company_name_manual = company_name_display,
            job_role            = job_role,
            job_description     = job_description,
            template            = template,
            source_resume_text  = source_resume_text,
        )
    except Exception as exc:
        logger.error(f"Resume generation exception: {exc}", exc_info=True)
        flash('AI generation encountered an error. Please try again.', 'danger')
        return redirect(url_for('resume_builder.create'))

    if result.get('error') and not result.get('content_json'):
        flash(f'Generation failed: {result["error"]}', 'danger')
        return redirect(url_for('resume_builder.create'))

    # ── Save to DB ───────────────────────────────────────────────────────────
    try:
        gen_id = GeneratedResumeModel.create(
            user_id          = user_id,
            source_resume_id = source_resume_id,
            company_id       = company_id,
            company_name     = company_name_display,
            job_role         = job_role,
            job_description  = job_description,
            template         = template,
            content_json     = result['content_json'],
            ats_score        = result['ats_score'],
            skill_match      = result['skill_match'],
            label            = result['label'],
        )
    except Exception as exc:
        logger.error(f"DB save failed: {exc}", exc_info=True)
        flash('Resume generated but could not be saved. Please try again.', 'danger')
        return redirect(url_for('resume_builder.create'))

    if result.get('error'):
        flash(f'Note: {result["error"]}', 'warning')

    log_activity(user_id, 'resume_generate',
                 f'Generated AI resume: {result["label"]}',
                 'generated_resume', gen_id)

    flash(f'AI resume generated! ATS Score: {result["ats_score"]}% ✅', 'success')
    return redirect(url_for('resume_builder.preview', gen_id=gen_id))


# ---------------------------------------------------------------------------
# GET /resume/preview/<id>
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/preview/<int:gen_id>')
@login_required
def preview(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resume_builder.create'))

    companies = CompanyModel.get_all(limit=50)
    return render_template('resume_preview.html', gen=gen, companies=companies)


# ---------------------------------------------------------------------------
# POST /resume/edit/<id>  — save manual edits
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/edit/<int:gen_id>', methods=['POST'])
@login_required
def edit(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        return jsonify({'success': False, 'message': 'Not found'}), 404

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    # Update the content_json with incoming edits
    content = dict(gen.get('content_json') or {})

    # Allowed editable sections
    EDITABLE = ('candidate', 'professional_summary', 'skills', 'education',
                 'experience', 'projects', 'certifications', 'achievements')
    changed = False
    for key in EDITABLE:
        if key in body:
            content[key] = body[key]
            changed = True

    if not changed:
        return jsonify({'success': False, 'message': 'No changes provided'}), 400

    try:
        GeneratedResumeModel.update_content(gen_id, user_id, content)
        log_activity(user_id, 'resume_edit', f'Edited AI resume #{gen_id}')
        return jsonify({'success': True})
    except Exception as exc:
        logger.error(f"Edit save error: {exc}")
        return jsonify({'success': False, 'message': 'Save failed'}), 500


# ---------------------------------------------------------------------------
# POST /resume/regenerate-section/<id>  — AJAX regen single section
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/regenerate-section/<int:gen_id>', methods=['POST'])
@login_required
def regenerate_section(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        return jsonify({'success': False, 'message': 'Not found'}), 404

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    section_name  = body.get('section', '')
    extra_context = body.get('context', '')
    ALLOWED_SECTIONS = ('professional_summary', 'skills', 'experience', 'projects')
    if section_name not in ALLOWED_SECTIONS:
        return jsonify({'success': False, 'message': f'Section {section_name!r} not regeneratable'}), 400

    content      = dict(gen.get('content_json') or {})
    company_name = gen.get('company_name') or 'the target company'
    job_role     = gen.get('job_role') or 'Software Engineer'

    try:
        from services.resume_generation_service import regenerate_section as regen_fn
        new_content = regen_fn(content, section_name, user_id,
                               company_name, job_role, extra_context)
        content[section_name] = new_content
        GeneratedResumeModel.update_content(gen_id, user_id, content)
        return jsonify({'success': True, 'content': new_content})
    except Exception as exc:
        logger.error(f"Section regen error: {exc}")
        return jsonify({'success': False, 'message': 'Regeneration failed'}), 500


# ---------------------------------------------------------------------------
# POST /resume/change-template/<id>  — AJAX template switch
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/change-template/<int:gen_id>', methods=['POST'])
@login_required
def change_template(gen_id):
    user_id = session['user_id']
    try:
        body     = request.get_json(force=True) or {}
        template = body.get('template', 'classic')
        if template not in ('classic', 'modern', 'minimal'):
            return jsonify({'success': False, 'message': 'Invalid template'}), 400
        GeneratedResumeModel.update_template(gen_id, user_id, template)
        return jsonify({'success': True})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /resume/download/pdf/<id>
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/download/pdf/<int:gen_id>')
@login_required
def download_pdf(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resume_builder.create'))

    import uuid
    from services.resume_generation_service import render_pdf

    out_dir  = _gen_dir(user_id)
    filename = f"resume_{gen_id}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(out_dir, filename)

    result = render_pdf(gen['content_json'], gen.get('template', 'classic'), out_path)
    if not result or not os.path.exists(out_path):
        flash('PDF generation failed. Please try again.', 'danger')
        return redirect(url_for('resume_builder.preview', gen_id=gen_id))

    dl_name = f"{gen.get('label','resume').replace(' — ', '_').replace(' ', '_')}.pdf"
    log_activity(user_id, 'resume_download_pdf', f'Downloaded PDF: {dl_name}')
    return send_file(out_path, download_name=dl_name, as_attachment=True)


# ---------------------------------------------------------------------------
# GET /resume/download/docx/<id>
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/download/docx/<int:gen_id>')
@login_required
def download_docx(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resume_builder.create'))

    import uuid
    from services.resume_generation_service import render_docx

    out_dir  = _gen_dir(user_id)
    filename = f"resume_{gen_id}_{uuid.uuid4().hex[:8]}.docx"
    out_path = os.path.join(out_dir, filename)

    result = render_docx(gen['content_json'], gen.get('template', 'classic'), out_path)
    if not result or not os.path.exists(out_path):
        flash('DOCX generation failed. Please try again.', 'danger')
        return redirect(url_for('resume_builder.preview', gen_id=gen_id))

    dl_name = f"{gen.get('label','resume').replace(' — ', '_').replace(' ', '_')}.docx"
    log_activity(user_id, 'resume_download_docx', f'Downloaded DOCX: {dl_name}')
    return send_file(out_path, download_name=dl_name, as_attachment=True)


# ---------------------------------------------------------------------------
# POST /resume/delete/<id>
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/delete/<int:gen_id>', methods=['POST'])
@login_required
def delete(gen_id):
    user_id = session['user_id']
    gen     = GeneratedResumeModel.get_by_id(gen_id, user_id)
    if not gen:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Not found'}), 404
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.index'))

    GeneratedResumeModel.soft_delete(gen_id, user_id)
    log_activity(user_id, 'resume_delete_ai', f'Deleted AI resume: {gen.get("label","")}')

    if request.is_json:
        return jsonify({'success': True})
    flash('AI resume deleted.', 'success')
    return redirect(url_for('resumes.index'))


# ---------------------------------------------------------------------------
# GET /resume/api/list  — JSON list for dashboard widget
# ---------------------------------------------------------------------------

@resume_builder_bp.route('/resume/api/list')
@login_required
def api_list():
    user_id = session['user_id']
    gens    = GeneratedResumeModel.get_all(user_id)
    return jsonify([{
        'id':         g['id'],
        'label':      g.get('label', ''),
        'company':    g.get('company_name', ''),
        'job_role':   g.get('job_role', ''),
        'ats_score':  g.get('ats_score', 0),
        'template':   g.get('template', 'classic'),
        'created_at': str(g.get('created_at', '')),
    } for g in gens])

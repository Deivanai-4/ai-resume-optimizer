"""Reports Blueprint."""
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from utils.decorators import login_required
from utils.helpers import log_activity, parse_json_field
from models.report import ReportModel
from models.analysis import AnalysisModel
from models.user import UserModel
from models.profile import ProfileModel
from services.pdf_service import generate_pdf_report

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def index():
    user_id = session['user_id']
    reports = ReportModel.get_all(user_id)
    analyses = AnalysisModel.get_all(user_id)
    averages = AnalysisModel.get_averages(user_id)
    
    return render_template('reports.html',
                           reports=reports,
                           analyses=analyses,
                           averages=averages)


@reports_bp.route('/reports/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    report_type = request.form.get('report_type', 'Career')
    analysis_id = request.form.get('analysis_id', type=int)
    
    user = UserModel.get_by_id(user_id)
    profile = ProfileModel.get(user_id)
    analysis = None
    
    if analysis_id:
        analysis = AnalysisModel.get_by_id(analysis_id, user_id)
    else:
        recent = AnalysisModel.get_latest(user_id)
        if recent:
            analysis = recent
    
    from database.db import query_db
    
    # Gather interview stats
    interview_stats = query_db(
        '''SELECT COUNT(*) as total, 
                  SUM(CASE WHEN user_answer IS NOT NULL AND user_answer != '' THEN 1 ELSE 0 END) as answered,
                  AVG(score) as avg_score
           FROM interview_questions WHERE user_id=%s''', 
        (user_id,), one=True
    )
    
    # Gather active roadmap
    roadmap = query_db(
        'SELECT * FROM learning_roadmaps WHERE user_id=%s ORDER BY created_at DESC LIMIT 1',
        (user_id,), one=True
    )
    
    from services.storage_service import (
        get_temp_dir, upload_report_file, get_private_download_url,
        is_cloudinary_id, delete_stored_file
    )
    import uuid
    filename = f'{report_type.lower()}_report_{uuid.uuid4().hex[:8]}.pdf'
    temp_dir = get_temp_dir()
    temp_pdf_path = os.path.join(temp_dir, filename)
    
    try:
        result = generate_pdf_report(
            user, profile, analysis, report_type, temp_pdf_path,
            interview_stats=interview_stats, roadmap=roadmap
        )
        
        if result and os.path.exists(temp_pdf_path):
            title = f"{report_type} Report - {user['full_name']}"
            stored_path = upload_report_file(temp_pdf_path, user_id, report_type)
            report_id = ReportModel.create(user_id, report_type, title, stored_path, 'PDF', analysis_id)
            log_activity(user_id, 'report_generate', f'Generated {report_type} Report')
            flash(f'{report_type} Report generated successfully! ✅', 'success')
            
            # Clean up temp file if uploaded to cloud
            if is_cloudinary_id(stored_path) and os.path.exists(temp_pdf_path):
                try:
                    os.remove(temp_pdf_path)
                except OSError:
                    pass
        else:
            flash('Report generation failed. reportlab may not be installed or generation error occurred.', 'danger')
    except Exception as e:
        current_app.logger.error(f"Report generation error: {e}")
        flash(f'Report generation error: {str(e)}', 'danger')
        if os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass
    
    return redirect(url_for('reports.index'))


@reports_bp.route('/reports/download/<int:report_id>')
@login_required
def download(report_id):
    user_id = session['user_id']
    report = ReportModel.get_by_id(report_id, user_id)
    
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('reports.index'))
    
    from services.storage_service import is_cloudinary_id, get_private_download_url
    path = report['file_path']

    if is_cloudinary_id(path):
        try:
            url = get_private_download_url(path, 'pdf')
            return redirect(url)
        except Exception as e:
            current_app.logger.error(f"Failed to generate report download URL: {e}")
            flash('Error generating secure download link.', 'danger')
            return redirect(url_for('reports.index'))
    else:
        if os.path.exists(path):
            return send_file(path,
                             download_name=f"{report['title']}.pdf",
                             as_attachment=True)
        flash('This report was stored on a previous server and is no longer available for download.', 'warning')
        return redirect(url_for('reports.index'))


@reports_bp.route('/reports/delete/<int:report_id>', methods=['POST'])
@login_required
def delete(report_id):
    user_id = session['user_id']
    report = ReportModel.get_by_id(report_id, user_id)
    if report:
        from services.storage_service import delete_stored_file
        delete_stored_file(report['file_path'], resource_type='raw', is_private=True)
        ReportModel.delete(report_id, user_id)
        flash('Report deleted.', 'success')
    return redirect(url_for('reports.index'))

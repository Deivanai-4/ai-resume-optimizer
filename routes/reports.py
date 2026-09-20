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
    elif report_type in ['ATS', 'Resume']:
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
    
    reports_dir = os.path.join('uploads', 'reports', str(user_id))
    os.makedirs(reports_dir, exist_ok=True)
    
    import uuid
    filename = f'{report_type.lower()}_report_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(reports_dir, filename)
    
    try:
        result = generate_pdf_report(
            user, profile, analysis, report_type, output_path,
            interview_stats=interview_stats, roadmap=roadmap
        )
        
        if result:
            title = f"{report_type} Report - {user['full_name']}"
            report_id = ReportModel.create(user_id, report_type, title, output_path, 'PDF', analysis_id)
            log_activity(user_id, 'report_generate', f'Generated {report_type} Report')
            flash(f'{report_type} Report generated successfully! ✅', 'success')
        else:
            flash('Report generation failed. reportlab may not be installed.', 'danger')
    except Exception as e:
        flash(f'Report generation error: {str(e)}', 'danger')
    
    return redirect(url_for('reports.index'))


@reports_bp.route('/reports/download/<int:report_id>')
@login_required
def download(report_id):
    user_id = session['user_id']
    report = ReportModel.get_by_id(report_id, user_id)
    
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('reports.index'))
    
    if not os.path.exists(report['file_path']):
        flash('Report file not found on server.', 'danger')
        return redirect(url_for('reports.index'))
    
    return send_file(report['file_path'],
                     download_name=f"{report['title']}.pdf",
                     as_attachment=True)


@reports_bp.route('/reports/delete/<int:report_id>', methods=['POST'])
@login_required
def delete(report_id):
    user_id = session['user_id']
    report = ReportModel.get_by_id(report_id, user_id)
    if report:
        try:
            if os.path.exists(report['file_path']):
                os.remove(report['file_path'])
        except Exception:
            pass
        ReportModel.delete(report_id, user_id)
        flash('Report deleted.', 'success')
    return redirect(url_for('reports.index'))

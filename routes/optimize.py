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
    
    # Pre-selected from query params
    resume_id = request.args.get('resume_id', type=int)
    
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
                           optimized=optimized,
                           preselect_resume=resume_id)


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


@optimize_bp.route('/optimize/download/<int:opt_id>/<fmt>')
@login_required
def download(opt_id, fmt):
    """Download an optimized resume as PDF, DOCX, or TXT."""
    user_id = session['user_id']
    fmt = fmt.lower()
    if fmt not in ('pdf', 'docx', 'txt'):
        flash('Invalid format requested.', 'danger')
        return redirect(url_for('optimize.index'))

    row = query_db(
        'SELECT * FROM optimized_resumes WHERE id=%s AND user_id=%s',
        (opt_id, user_id), one=True
    )
    if not row:
        flash('Optimized resume not found.', 'danger')
        return redirect(url_for('optimize.index'))

    text = (row.get('optimized_text') or '').strip()
    filename_base = f'Tailored_Resume_{opt_id}'

    # ── TXT ──────────────────────────────────────────────────────────
    if fmt == 'txt':
        from flask import Response
        return Response(
            text,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.txt"'}
        )

    # ── DOCX ─────────────────────────────────────────────────────────
    if fmt == 'docx':
        import io
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from flask import send_file

        doc = Document()

        # Page margins
        for section in doc.sections:
            section.top_margin    = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin   = Inches(1.0)
            section.right_margin  = Inches(1.0)

        # Remove default paragraph spacing
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        def set_para_spacing(para, before=0, after=0):
            pPr = para._p.get_or_add_pPr()
            spacing = OxmlElement('w:spacing')
            spacing.set(qn('w:before'), str(before))
            spacing.set(qn('w:after'), str(after))
            pPr.append(spacing)

        HEADING_COLOR = RGBColor(0x1E, 0x40, 0xAF)  # indigo-800

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                p = doc.add_paragraph()
                set_para_spacing(p, before=0, after=40)
                continue

            # Detect section headings (ALL CAPS or ends with ':')
            is_heading = (
                line.isupper() and len(line) > 2
                or (line.endswith(':') and len(line.split()) <= 5)
            )

            if is_heading:
                p = doc.add_paragraph()
                set_para_spacing(p, before=120, after=40)
                run = p.add_run(line)
                run.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = HEADING_COLOR
                # Underline the heading
                from docx.oxml import OxmlElement as OE
                rPr = run._r.get_or_add_rPr()
                u = OE('w:u')
                u.set(qn('w:val'), 'single')
                rPr.append(u)
            elif line.startswith('•') or line.startswith('-'):
                p = doc.add_paragraph(style='List Bullet')
                set_para_spacing(p, before=0, after=20)
                run = p.add_run(line.lstrip('•- ').strip())
                run.font.size = Pt(10.5)
            else:
                p = doc.add_paragraph()
                set_para_spacing(p, before=0, after=20)
                run = p.add_run(line)
                run.font.size = Pt(10.5)

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f'{filename_base}.docx'
        )

    # ── PDF ──────────────────────────────────────────────────────────
    if fmt == 'pdf':
        import io
        from flask import send_file
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2.5*cm, rightMargin=2.5*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        INDIGO = colors.HexColor('#1E40AF')

        style_body = ParagraphStyle(
            'body', parent=styles['Normal'],
            fontSize=10.5, leading=16, spaceAfter=4,
            textColor=colors.HexColor('#1e293b')
        )
        style_heading = ParagraphStyle(
            'heading', parent=styles['Normal'],
            fontSize=11.5, leading=16, spaceBefore=14, spaceAfter=4,
            textColor=INDIGO, fontName='Helvetica-Bold',
            borderPadding=(0, 0, 2, 0),
        )
        style_bullet = ParagraphStyle(
            'bullet', parent=styles['Normal'],
            fontSize=10.5, leading=15, spaceAfter=3,
            leftIndent=14, bulletIndent=0,
            textColor=colors.HexColor('#1e293b')
        )

        story = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # Escape XML chars
            safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            is_heading = (
                line.isupper() and len(line) > 2
                or (line.endswith(':') and len(line.split()) <= 5)
            )

            if is_heading:
                story.append(Paragraph(f'<u>{safe}</u>', style_heading))
            elif line.startswith('•') or line.startswith('-'):
                bullet_text = '• ' + safe.lstrip('•- ').strip()
                story.append(Paragraph(bullet_text, style_bullet))
            else:
                story.append(Paragraph(safe, style_body))

        doc.build(story)
        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{filename_base}.pdf'
        )


"""
PDF/DOCX Report Generation Service
"""
import os
import json
from datetime import datetime


def generate_pdf_report(user, profile, analysis, report_type='Career', output_path=None, interview_stats=None, roadmap=None):
    """Generate a PDF report using reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        if not output_path:
            return None
        
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=50, leftMargin=50,
                                topMargin=60, bottomMargin=60)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=22, textColor=colors.HexColor('#4F46E5'),
                                     spaceAfter=6, alignment=TA_CENTER)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                       fontSize=14, textColor=colors.HexColor('#1E293B'),
                                       spaceBefore=12, spaceAfter=6)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                    fontSize=10, textColor=colors.HexColor('#475569'),
                                    spaceAfter=4, leading=16)
        
        # Header
        story.append(Paragraph("AI Career Intelligence Platform", title_style))
        story.append(Paragraph(f"{report_type} Report", 
                               ParagraphStyle('Sub', parent=styles['Normal'], 
                                              fontSize=14, alignment=TA_CENTER,
                                              textColor=colors.HexColor('#64748B'))))
        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4F46E5')))
        story.append(Spacer(1, 0.2 * inch))
        
        # Student Info
        story.append(Paragraph("Student Information", heading_style))
        name = user.get('full_name', 'N/A')
        email = user.get('email', 'N/A')
        story.append(Paragraph(f"<b>Name:</b> {name}", body_style))
        story.append(Paragraph(f"<b>Email:</b> {email}", body_style))
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
        story.append(Spacer(1, 0.2 * inch))
        
        if analysis:
            # Scores Section
            story.append(Paragraph("Analysis Scores", heading_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0')))
            story.append(Spacer(1, 0.1 * inch))
            
            score_data = [
                ['Metric', 'Score', 'Status'],
                ['ATS Score', f"{analysis.get('ats_score', 0)}%", _get_status(analysis.get('ats_score', 0))],
                ['Skill Match', f"{analysis.get('skill_match_score', 0)}%", _get_status(analysis.get('skill_match_score', 0))],
                ['Tech Match', f"{analysis.get('tech_match_score', 0)}%", _get_status(analysis.get('tech_match_score', 0))],
                ['Career Readiness', f"{analysis.get('career_readiness_score', 0)}%", _get_status(analysis.get('career_readiness_score', 0))],
                ['Overall Score', f"{analysis.get('overall_score', 0)}%", _get_status(analysis.get('overall_score', 0))],
            ]
            
            t = Table(score_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))
            
            # Strengths
            strengths = _parse_json_field(analysis.get('strengths'))
            if strengths:
                story.append(Paragraph("Key Strengths", heading_style))
                for s in strengths[:5]:
                    story.append(Paragraph(f"✓ {s}", body_style))
                story.append(Spacer(1, 0.15 * inch))
            
            # Weaknesses
            weaknesses = _parse_json_field(analysis.get('weaknesses'))
            if weaknesses:
                story.append(Paragraph("Areas for Improvement", heading_style))
                for w in weaknesses[:5]:
                    story.append(Paragraph(f"• {w}", body_style))
                story.append(Spacer(1, 0.15 * inch))
            
            # Missing Skills
            missing = _parse_json_field(analysis.get('missing_skills'))
            if missing:
                story.append(Paragraph("Missing Skills to Develop", heading_style))
                story.append(Paragraph(', '.join(missing[:8]), body_style))
                story.append(Spacer(1, 0.15 * inch))
            
            # Suggestions
            suggestions = _parse_json_field(analysis.get('resume_suggestions'))
            if suggestions:
                story.append(Paragraph("Resume Improvement Suggestions", heading_style))
                for i, sug in enumerate(suggestions[:5], 1):
                    story.append(Paragraph(f"{i}. {sug}", body_style))

        # Career Readiness & Activity
        story.append(Spacer(1, 0.2 * inch))
        if interview_stats and interview_stats.get('total', 0) > 0:
            story.append(Paragraph("Interview Readiness", heading_style))
            total = interview_stats.get('total', 0)
            answered = interview_stats.get('answered', 0)
            score = interview_stats.get('avg_score') or 0
            story.append(Paragraph(f"<b>Questions Generated:</b> {total}", body_style))
            story.append(Paragraph(f"<b>Questions Answered:</b> {answered}", body_style))
            if score > 0:
                story.append(Paragraph(f"<b>Average Answer Score:</b> {float(score):.1f}%", body_style))
            story.append(Spacer(1, 0.15 * inch))

        if roadmap:
            story.append(Paragraph("Learning Roadmap Progress", heading_style))
            story.append(Paragraph(f"<b>Current Roadmap:</b> {roadmap.get('title', 'N/A')}", body_style))
            story.append(Paragraph(f"<b>Status:</b> {roadmap.get('status', 'Active')}", body_style))
            story.append(Paragraph(f"<b>Completion:</b> {roadmap.get('completion_percent', 0)}%", body_style))
            story.append(Spacer(1, 0.15 * inch))
        
        # Footer
        story.append(Spacer(1, 0.4 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0')))
        story.append(Paragraph(
            "Generated by AI Career Intelligence Platform | Confidential Student Report",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                           textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER)
        ))
        
        doc.build(story)
        return output_path
        
    except ImportError:
        return None
    except Exception as e:
        return None


def _get_status(score):
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    return "Needs Work"


def _parse_json_field(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []

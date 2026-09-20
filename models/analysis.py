"""Analysis model."""
from database.db import query_db, execute_db
import json


class AnalysisModel:

    @staticmethod
    def create(user_id, resume_id, company_id, job_title, scores, ai_data):
        analysis_id = execute_db(
            '''INSERT INTO resume_analysis (user_id, resume_id, company_id, job_title,
               ats_score, skill_match_score, tech_match_score, project_match_score,
               career_readiness_score, interview_readiness_score, strengths, weaknesses,
               missing_skills, resume_suggestions, resume_summary, keyword_analysis,
               grammar_score, formatting_score, overall_score, analysis_data)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, resume_id, company_id, job_title,
             scores.get('ats_score', 0), scores.get('skill_match_score', 0),
             scores.get('tech_match_score', 0), scores.get('project_match_score', 0),
             scores.get('career_readiness_score', 0), scores.get('interview_readiness_score', 0),
             json.dumps(ai_data.get('strengths', [])), json.dumps(ai_data.get('weaknesses', [])),
             json.dumps(ai_data.get('missing_skills', [])), json.dumps(ai_data.get('suggestions', [])),
             ai_data.get('summary', ''), json.dumps(ai_data.get('keywords', [])),
             scores.get('grammar_score', 0), scores.get('formatting_score', 0),
             scores.get('overall_score', 0), json.dumps(ai_data)),
            get_id=True
        )
        return analysis_id

    @staticmethod
    def get_by_id(analysis_id, user_id):
        return query_db(
            'SELECT * FROM resume_analysis WHERE id=%s AND user_id=%s',
            (analysis_id, user_id), one=True
        )

    @staticmethod
    def get_latest(user_id):
        return query_db(
            '''SELECT ra.*, c.name as company_name, r.original_name as resume_name
               FROM resume_analysis ra
               LEFT JOIN companies c ON ra.company_id = c.id
               LEFT JOIN resumes r ON ra.resume_id = r.id
               WHERE ra.user_id=%s ORDER BY ra.created_at DESC LIMIT 1''',
            (user_id,), one=True
        )

    @staticmethod
    def get_recent(user_id, limit=5):
        return query_db(
            '''SELECT ra.*, c.name as company_name, r.original_name as resume_name
               FROM resume_analysis ra
               LEFT JOIN companies c ON ra.company_id = c.id
               LEFT JOIN resumes r ON ra.resume_id = r.id
               WHERE ra.user_id=%s ORDER BY ra.created_at DESC LIMIT %s''',
            (user_id, limit)
        )

    @staticmethod
    def get_averages(user_id):
        return query_db(
            '''SELECT AVG(ats_score) as avg_ats, AVG(skill_match_score) as avg_skill,
               AVG(tech_match_score) as avg_tech, AVG(career_readiness_score) as avg_career,
               AVG(overall_score) as avg_overall, COUNT(*) as total_analyses
               FROM resume_analysis WHERE user_id=%s''',
            (user_id,), one=True
        )

    @staticmethod
    def get_all(user_id):
        return query_db(
            '''SELECT ra.*, c.name as company_name, r.original_name as resume_name
               FROM resume_analysis ra
               LEFT JOIN companies c ON ra.company_id = c.id
               LEFT JOIN resumes r ON ra.resume_id = r.id
               WHERE ra.user_id=%s ORDER BY ra.created_at DESC''',
            (user_id,)
        )

    @staticmethod
    def get_for_resume_company(resume_id, company_id):
        return query_db(
            'SELECT * FROM resume_analysis WHERE resume_id=%s AND company_id=%s ORDER BY created_at DESC LIMIT 1',
            (resume_id, company_id), one=True
        )

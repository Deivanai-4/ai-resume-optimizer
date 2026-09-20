"""Resume model."""
from database.db import query_db, execute_db
import json


class ResumeModel:

    @staticmethod
    def get_all(user_id):
        return query_db(
            'SELECT * FROM resumes WHERE user_id=%s AND is_active=1 ORDER BY upload_date DESC',
            (user_id,)
        )

    @staticmethod
    def get_by_id(resume_id, user_id):
        return query_db(
            'SELECT * FROM resumes WHERE id=%s AND user_id=%s AND is_active=1',
            (resume_id, user_id), one=True
        )

    @staticmethod
    def create(user_id, file_name, original_name, file_path, file_size, file_type):
        resume_id = execute_db(
            '''INSERT INTO resumes (user_id, file_name, original_name, file_path, file_size, file_type)
               VALUES (%s,%s,%s,%s,%s,%s)''',
            (user_id, file_name, original_name, file_path, file_size, file_type),
            get_id=True
        )
        # Update resume count
        execute_db(
            'UPDATE student_profiles SET resume_count = resume_count + 1 WHERE user_id=%s',
            (user_id,)
        )
        return resume_id

    @staticmethod
    def update_parsed_data(resume_id, extracted_text, extracted_skills):
        skills_json = json.dumps(extracted_skills) if isinstance(extracted_skills, list) else extracted_skills
        execute_db(
            'UPDATE resumes SET extracted_text=%s, extracted_skills=%s, is_parsed=1 WHERE id=%s',
            (extracted_text, skills_json, resume_id)
        )

    @staticmethod
    def delete(resume_id, user_id):
        execute_db(
            'UPDATE resumes SET is_active=0 WHERE id=%s AND user_id=%s',
            (resume_id, user_id)
        )
        execute_db(
            'UPDATE student_profiles SET resume_count = GREATEST(0, resume_count - 1) WHERE user_id=%s',
            (user_id,)
        )

    @staticmethod
    def get_latest(user_id):
        return query_db(
            'SELECT * FROM resumes WHERE user_id=%s AND is_active=1 ORDER BY upload_date DESC LIMIT 1',
            (user_id,), one=True
        )

    @staticmethod
    def count(user_id):
        result = query_db(
            'SELECT COUNT(*) as cnt FROM resumes WHERE user_id=%s AND is_active=1',
            (user_id,), one=True
        )
        return result['cnt'] if result else 0

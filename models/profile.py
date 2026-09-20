"""Profile model — Student profile CRUD."""
from database.db import query_db, execute_db
import json


class ProfileModel:

    @staticmethod
    def create_default(user_id):
        execute_db('INSERT INTO student_profiles (user_id) VALUES (%s)', (user_id,))

    @staticmethod
    def get(user_id):
        return query_db('SELECT * FROM student_profiles WHERE user_id = %s', (user_id,), one=True)

    @staticmethod
    def update_basic(user_id, data):
        execute_db(
            '''UPDATE student_profiles SET phone=%s, date_of_birth=%s, gender=%s,
               location=%s, career_objective=%s, updated_at=NOW()
               WHERE user_id=%s''',
            (data.get('phone'), data.get('date_of_birth') or None,
             data.get('gender'), data.get('location'), data.get('career_objective'), user_id)
        )
        execute_db(
            'UPDATE users SET full_name=%s WHERE id=%s',
            (data.get('full_name'), user_id)
        )

    @staticmethod
    def update_links(user_id, github_url, linkedin_url, portfolio_url):
        execute_db(
            '''UPDATE student_profiles SET github_url=%s, linkedin_url=%s, portfolio_url=%s
               WHERE user_id=%s''',
            (github_url, linkedin_url, portfolio_url, user_id)
        )

    @staticmethod
    def update_photo(user_id, photo_path):
        execute_db(
            'UPDATE student_profiles SET photo_path=%s WHERE user_id=%s',
            (photo_path, user_id)
        )

    @staticmethod
    def calculate_completion(user_id):
        """Calculate profile completion percentage."""
        profile = query_db('SELECT * FROM student_profiles WHERE user_id=%s', (user_id,), one=True)
        user = query_db('SELECT * FROM users WHERE id=%s', (user_id,), one=True)
        if not profile or not user:
            return 0
        
        fields = [
            user.get('full_name'), user.get('email'),
            profile.get('phone'), profile.get('date_of_birth'),
            profile.get('location'), profile.get('career_objective'),
            profile.get('github_url') or profile.get('linkedin_url'),
            profile.get('photo_path')
        ]
        
        has_education = query_db('SELECT id FROM education WHERE user_id=%s LIMIT 1', (user_id,), one=True)
        has_skills = query_db('SELECT id FROM skills WHERE user_id=%s LIMIT 1', (user_id,), one=True)
        has_projects = query_db('SELECT id FROM projects WHERE user_id=%s LIMIT 1', (user_id,), one=True)
        has_resumes = query_db('SELECT id FROM resumes WHERE user_id=%s LIMIT 1', (user_id,), one=True)
        
        filled = sum(1 for f in fields if f) + (1 if has_education else 0) + \
                 (1 if has_skills else 0) + (1 if has_projects else 0) + (1 if has_resumes else 0)
        total = len(fields) + 4
        completion = int((filled / total) * 100)
        
        execute_db('UPDATE student_profiles SET profile_completion=%s WHERE user_id=%s', (completion, user_id))
        return completion

    # --- SKILLS ---
    @staticmethod
    def get_skills(user_id):
        return query_db('SELECT * FROM skills WHERE user_id=%s ORDER BY category, skill_name', (user_id,))

    @staticmethod
    def add_skill(user_id, skill_name, category, proficiency, proficiency_percent):
        return execute_db(
            'INSERT INTO skills (user_id, skill_name, category, proficiency, proficiency_percent) VALUES (%s,%s,%s,%s,%s)',
            (user_id, skill_name, category, proficiency, proficiency_percent), get_id=True
        )

    @staticmethod
    def delete_skill(skill_id, user_id):
        execute_db('DELETE FROM skills WHERE id=%s AND user_id=%s', (skill_id, user_id))

    # --- EDUCATION ---
    @staticmethod
    def get_education(user_id):
        return query_db('SELECT * FROM education WHERE user_id=%s ORDER BY end_year DESC', (user_id,))

    @staticmethod
    def add_education(user_id, data):
        return execute_db(
            '''INSERT INTO education (user_id, degree, field_of_study, institution, university,
               start_year, end_year, cgpa, percentage, is_current, description)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, data.get('degree'), data.get('field_of_study'), data.get('institution'),
             data.get('university'), data.get('start_year') or None, data.get('end_year') or None,
             data.get('cgpa') or None, data.get('percentage') or None,
             1 if data.get('is_current') else 0, data.get('description')), get_id=True
        )

    @staticmethod
    def delete_education(edu_id, user_id):
        execute_db('DELETE FROM education WHERE id=%s AND user_id=%s', (edu_id, user_id))

    # --- PROJECTS ---
    @staticmethod
    def get_projects(user_id):
        return query_db('SELECT * FROM projects WHERE user_id=%s ORDER BY created_at DESC', (user_id,))

    @staticmethod
    def add_project(user_id, data):
        return execute_db(
            '''INSERT INTO projects (user_id, title, description, technologies, github_url, live_url)
               VALUES (%s,%s,%s,%s,%s,%s)''',
            (user_id, data.get('title'), data.get('description'), data.get('technologies'),
             data.get('github_url'), data.get('live_url')),
            get_id=True
        )

    @staticmethod
    def delete_project(proj_id, user_id):
        execute_db('DELETE FROM projects WHERE id=%s AND user_id=%s', (proj_id, user_id))

    # --- CERTIFICATIONS ---
    @staticmethod
    def get_certifications(user_id):
        return query_db('SELECT * FROM certifications WHERE user_id=%s ORDER BY issue_date DESC', (user_id,))

    @staticmethod
    def add_certification(user_id, data):
        return execute_db(
            '''INSERT INTO certifications (user_id, cert_name, issuing_org, issue_date, expiry_date, credential_id, credential_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, data.get('cert_name'), data.get('issuing_org'),
             data.get('issue_date') or None, data.get('expiry_date') or None,
             data.get('credential_id'), data.get('credential_url')), get_id=True
        )

    @staticmethod
    def delete_certification(cert_id, user_id):
        execute_db('DELETE FROM certifications WHERE id=%s AND user_id=%s', (cert_id, user_id))

    # --- EXPERIENCE ---
    @staticmethod
    def get_experience(user_id):
        return query_db('SELECT * FROM experience WHERE user_id=%s ORDER BY start_date DESC', (user_id,))

    @staticmethod
    def add_experience(user_id, data):
        return execute_db(
            '''INSERT INTO experience (user_id, job_title, company_name, location, start_date, end_date, is_current, description)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, data.get('job_title'), data.get('company_name'), data.get('location'),
             data.get('start_date') or None, data.get('end_date') or None,
             1 if data.get('is_current') else 0, data.get('description')), get_id=True
        )

    @staticmethod
    def delete_experience(exp_id, user_id):
        execute_db('DELETE FROM experience WHERE id=%s AND user_id=%s', (exp_id, user_id))

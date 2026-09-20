"""Company model."""
from database.db import query_db, execute_db


class CompanyModel:

    @staticmethod
    def search(query):
        q = f'%{query}%'
        return query_db(
            '''SELECT * FROM companies WHERE name LIKE %s OR industry LIKE %s OR location LIKE %s
               ORDER BY name LIMIT 20''',
            (q, q, q)
        )

    @staticmethod
    def get_all(limit=20):
        return query_db('SELECT * FROM companies ORDER BY name LIMIT %s', (limit,))

    @staticmethod
    def get_by_id(company_id):
        return query_db('SELECT * FROM companies WHERE id=%s', (company_id,), one=True)

    @staticmethod
    def get_by_slug(slug):
        return query_db('SELECT * FROM companies WHERE slug=%s', (slug,), one=True)

    @staticmethod
    def get_skills(company_id):
        return query_db(
            'SELECT * FROM company_skills WHERE company_id=%s ORDER BY importance, category',
            (company_id,)
        )

    @staticmethod
    def get_jobs(company_id):
        return query_db(
            'SELECT * FROM company_jobs WHERE company_id=%s AND is_active=1 ORDER BY posted_date DESC',
            (company_id,)
        )

    @staticmethod
    def get_required_skills_list(company_id):
        """Return a flat list of skill names."""
        skills = query_db(
            'SELECT skill_name FROM company_skills WHERE company_id=%s',
            (company_id,)
        )
        return [s['skill_name'] for s in skills]

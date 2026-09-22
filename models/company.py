"""Company model."""
import re
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

    # ------------------------------------------------------------------ #
    # AI-powered helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def search_by_name(name: str):
        """
        Case-insensitive exact + partial name lookup.
        Returns the best-matching company row, or None.
        """
        name = name.strip()
        # Try exact case-insensitive match first
        row = query_db(
            'SELECT * FROM companies WHERE LOWER(name) = LOWER(%s) LIMIT 1',
            (name,), one=True
        )
        if row:
            return row
        # Fall back to LIKE (e.g. 'TCS' matches 'Tata Consultancy Services')
        q = f'%{name}%'
        return query_db(
            'SELECT * FROM companies WHERE name LIKE %s LIMIT 1',
            (q,), one=True
        )

    @staticmethod
    def create_from_ai(profile_data: dict, ai_profile_json: str):
        """
        Insert a new company row from the AI-generated profile dict.
        Returns the newly created company row dict, or None on failure.

        Expected profile_data structure (matches the Qwen JSON schema):
          {
            "company": { name, official_name, industry, headquarters,
                         website, description, company_type, company_size,
                         founded_year, ... },
            "workplace": { company_culture, ... },
            ...
          }
        """
        co = profile_data.get('company', {})
        name = co.get('name', 'Unknown')

        # Build a URL-safe slug
        slug_base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        slug = slug_base

        # Ensure slug uniqueness by appending a counter
        counter = 1
        while query_db('SELECT id FROM companies WHERE slug=%s', (slug,), one=True):
            slug = f'{slug_base}-{counter}'
            counter += 1

        # Map company_type to the DB ENUM values
        allowed_types = {'Public', 'Private', 'MNC', 'Startup', 'Government'}
        raw_type = co.get('company_type', 'Private')
        company_type = raw_type if raw_type in allowed_types else 'Private'

        # founded_year must be int or None
        try:
            founded_year = int(str(co.get('founded_year', '') or '').strip())
        except (ValueError, TypeError):
            founded_year = None

        workplace = profile_data.get('workplace', {})
        headquarters = (
            co.get('headquarters')
            or (co.get('locations') or [None])[0]
            or ''
        )

        new_id = execute_db(
            '''INSERT INTO companies
               (name, slug, website, industry, location, description,
                founded_year, employee_count, company_type, culture, ai_profile)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (
                name,
                slug,
                co.get('website') or '',
                co.get('industry') or '',
                headquarters,
                co.get('description') or '',
                founded_year,
                co.get('company_size') or '',
                company_type,
                workplace.get('company_culture') or '',
                ai_profile_json,
            ),
            get_id=True
        )

        if not new_id:
            return None
        return query_db('SELECT * FROM companies WHERE id=%s', (new_id,), one=True)

    @staticmethod
    def save_skills_from_ai(company_id: int, technology: dict):
        """
        Bulk-insert company_skills rows from the AI 'technology' block.
        Wipes existing skills for this company first to avoid duplicates.
        """
        execute_db('DELETE FROM company_skills WHERE company_id=%s', (company_id,))

        # Map Qwen JSON keys → DB category values
        category_map = {
            'programming_languages': 'Programming',
            'frameworks':            'Framework',
            'databases':             'Database',
            'cloud_platforms':       'Cloud',
            'developer_tools':       'Tool',
            'tech_stack':            'Other',
        }

        seen = set()
        for field, category in category_map.items():
            for skill in (technology.get(field) or []):
                skill = str(skill).strip()
                if skill and skill.lower() not in seen:
                    seen.add(skill.lower())
                    execute_db(
                        '''INSERT INTO company_skills
                           (company_id, skill_name, category, importance)
                           VALUES (%s, %s, %s, %s)''',
                        (company_id, skill, category, 'Required')
                    )

    @staticmethod
    def update_ai_profile(company_id: int, ai_profile_json: str):
        """Persist the AI profile JSON blob for an existing company."""
        execute_db(
            'UPDATE companies SET ai_profile=%s WHERE id=%s',
            (ai_profile_json, company_id)
        )

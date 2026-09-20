"""
Generated Resume Model
======================
CRUD for the generated_resumes table.
"""
import json
import logging
from database.db import query_db, execute_db

logger = logging.getLogger(__name__)


class GeneratedResumeModel:

    @staticmethod
    def create(user_id, source_resume_id, company_id, company_name,
               job_role, job_description, template, content_json,
               ats_score, skill_match, label):
        """Insert a new generated resume row and return its id."""
        content_str = json.dumps(content_json) if isinstance(content_json, dict) else (content_json or '{}')
        resume_id = execute_db(
            '''INSERT INTO generated_resumes
               (user_id, source_resume_id, company_id, company_name, job_role,
                job_description, template, content_json, ats_score, skill_match, label)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user_id, source_resume_id, company_id, company_name, job_role,
             job_description, template, content_str, ats_score, skill_match, label),
            get_id=True
        )
        return resume_id

    @staticmethod
    def get_by_id(resume_id, user_id):
        row = query_db(
            'SELECT * FROM generated_resumes WHERE id=%s AND user_id=%s AND is_active=1',
            (resume_id, user_id), one=True
        )
        return GeneratedResumeModel._parse(row)

    @staticmethod
    def get_all(user_id):
        rows = query_db(
            '''SELECT * FROM generated_resumes
               WHERE user_id=%s AND is_active=1
               ORDER BY created_at DESC''',
            (user_id,)
        )
        return [GeneratedResumeModel._parse(r) for r in (rows or [])]

    @staticmethod
    def update_content(resume_id, user_id, content_json, template=None,
                       ats_score=None, skill_match=None, label=None):
        content_str = json.dumps(content_json) if isinstance(content_json, dict) else (content_json or '{}')
        sets = ['content_json=%s', 'updated_at=NOW()']
        vals = [content_str]
        if template:
            sets.append('template=%s'); vals.append(template)
        if ats_score is not None:
            sets.append('ats_score=%s'); vals.append(ats_score)
        if skill_match is not None:
            sets.append('skill_match=%s'); vals.append(skill_match)
        if label is not None:
            sets.append('label=%s'); vals.append(label)
        vals += [resume_id, user_id]
        execute_db(
            f"UPDATE generated_resumes SET {', '.join(sets)} WHERE id=%s AND user_id=%s",
            tuple(vals)
        )

    @staticmethod
    def update_template(resume_id, user_id, template):
        execute_db(
            'UPDATE generated_resumes SET template=%s WHERE id=%s AND user_id=%s',
            (template, resume_id, user_id)
        )

    @staticmethod
    def soft_delete(resume_id, user_id):
        execute_db(
            'UPDATE generated_resumes SET is_active=0 WHERE id=%s AND user_id=%s',
            (resume_id, user_id)
        )

    @staticmethod
    def count(user_id):
        result = query_db(
            'SELECT COUNT(*) as cnt FROM generated_resumes WHERE user_id=%s AND is_active=1',
            (user_id,), one=True
        )
        return result['cnt'] if result else 0

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse(row):
        """Parse content_json field from string to dict."""
        if not row:
            return None
        row = dict(row)
        if isinstance(row.get('content_json'), str):
            try:
                row['content_json'] = json.loads(row['content_json'])
            except (json.JSONDecodeError, TypeError):
                row['content_json'] = {}
        return row

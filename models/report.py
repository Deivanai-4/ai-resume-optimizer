"""Report model."""
from database.db import query_db, execute_db


class ReportModel:

    @staticmethod
    def create(user_id, report_type, title, file_path, file_format, analysis_id=None):
        return execute_db(
            'INSERT INTO reports (user_id, report_type, title, file_path, file_format, analysis_id) VALUES (%s,%s,%s,%s,%s,%s)',
            (user_id, report_type, title, file_path, file_format, analysis_id), get_id=True
        )

    @staticmethod
    def get_all(user_id):
        return query_db(
            'SELECT * FROM reports WHERE user_id=%s ORDER BY created_at DESC',
            (user_id,)
        )

    @staticmethod
    def get_by_id(report_id, user_id):
        return query_db(
            'SELECT * FROM reports WHERE id=%s AND user_id=%s',
            (report_id, user_id), one=True
        )

    @staticmethod
    def delete(report_id, user_id):
        execute_db('DELETE FROM reports WHERE id=%s AND user_id=%s', (report_id, user_id))

"""Roadmap model."""
from database.db import query_db, execute_db
import json


class RoadmapModel:

    @staticmethod
    def create(user_id, company_id, resume_id, title, total_weeks=12):
        return execute_db(
            '''INSERT INTO learning_roadmaps (user_id, company_id, resume_id, title, total_duration_weeks)
               VALUES (%s,%s,%s,%s,%s)''',
            (user_id, company_id, resume_id, title, total_weeks), get_id=True
        )

    @staticmethod
    def get_latest(user_id):
        return query_db(
            '''SELECT lr.*, c.name as company_name
               FROM learning_roadmaps lr
               LEFT JOIN companies c ON lr.company_id = c.id
               WHERE lr.user_id=%s ORDER BY lr.created_at DESC LIMIT 1''',
            (user_id,), one=True
        )

    @staticmethod
    def get_all(user_id):
        return query_db(
            '''SELECT lr.*, c.name as company_name
               FROM learning_roadmaps lr
               LEFT JOIN companies c ON lr.company_id = c.id
               WHERE lr.user_id=%s ORDER BY lr.created_at DESC''',
            (user_id,)
        )

    @staticmethod
    def get_by_id(roadmap_id, user_id):
        return query_db(
            '''SELECT lr.*, c.name as company_name
               FROM learning_roadmaps lr
               LEFT JOIN companies c ON lr.company_id = c.id
               WHERE lr.id=%s AND lr.user_id=%s''',
            (roadmap_id, user_id), one=True
        )

    @staticmethod
    def get_items(roadmap_id):
        return query_db(
            'SELECT * FROM roadmap_items WHERE roadmap_id=%s ORDER BY order_index',
            (roadmap_id,)
        )

    @staticmethod
    def add_item(roadmap_id, skill_name, priority, duration_weeks, order_index, resources=None, youtube=None, docs=None, projects=None):
        return execute_db(
            '''INSERT INTO roadmap_items (roadmap_id, skill_name, priority, duration_weeks,
               order_index, resources, youtube_links, doc_links, project_ideas)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (roadmap_id, skill_name, priority, duration_weeks, order_index,
             resources, youtube, docs, projects), get_id=True
        )

    @staticmethod
    def update_item_status(item_id, status):
        execute_db('UPDATE roadmap_items SET status=%s WHERE id=%s', (status, item_id))

    @staticmethod
    def update_completion(roadmap_id):
        result = query_db(
            '''SELECT COUNT(*) as total,
               SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) as completed
               FROM roadmap_items WHERE roadmap_id=%s''',
            (roadmap_id,), one=True
        )
        if result and result['total'] > 0:
            pct = int((result['completed'] / result['total']) * 100)
            execute_db('UPDATE learning_roadmaps SET completion_percent=%s WHERE id=%s', (pct, roadmap_id))
            return pct
        return 0

from app import create_app
from database.db import get_db, query_db
from models.report import ReportModel
import os
import uuid

app = create_app()
with app.app_context():
    users = query_db('SELECT id FROM users LIMIT 1')
    if users:
        user_id = users[0]['id']
        try:
            report_id = ReportModel.create(user_id, 'Career', 'Test Report', 'uploads/test.pdf', 'PDF', None)
            print(f"Report created with ID: {report_id}")
        except Exception as e:
            print(f"Exception: {str(e)}")

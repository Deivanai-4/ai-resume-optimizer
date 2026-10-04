from app import create_app
from database.db import get_db, query_db
from models.user import UserModel
from models.profile import ProfileModel
from models.analysis import AnalysisModel
from services.pdf_service import generate_pdf_report
import os
import uuid

app = create_app()
with app.app_context():
    users = query_db('SELECT id FROM users LIMIT 1')
    if users:
        user_id = users[0]['id']
        user = UserModel.get_by_id(user_id)
        profile = ProfileModel.get(user_id)
        analysis = AnalysisModel.get_latest(user_id)
        reports_dir = os.path.join('uploads', 'reports', str(user_id))
        os.makedirs(reports_dir, exist_ok=True)
        filename = f'career_report_{uuid.uuid4().hex[:8]}.pdf'
        output_path = os.path.join(reports_dir, filename)
        
        result = generate_pdf_report(user, profile, analysis, 'Career', output_path)
        print(f"Result: {result}")
        if result is None:
            print("Failed to generate PDF")

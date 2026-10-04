from app import create_app
from database.db import get_db, query_db
from models.user import UserModel
from models.profile import ProfileModel
from models.analysis import AnalysisModel
from services.pdf_service import generate_pdf_report
import os
import uuid
import traceback

app = create_app()
with app.app_context():
    users = query_db('SELECT id FROM users LIMIT 1')
    if users:
        user_id = users[0]['id']
        user = UserModel.get_by_id(user_id)
        profile = ProfileModel.get(user_id)
        analysis = AnalysisModel.get_latest(user_id)
        
        interview_stats = query_db(
            '''SELECT COUNT(*) as total, 
                      SUM(CASE WHEN user_answer IS NOT NULL AND user_answer != '' THEN 1 ELSE 0 END) as answered,
                      AVG(score) as avg_score
               FROM interview_questions WHERE user_id=%s''', 
            (user_id,), one=True
        )
        
        roadmap = query_db(
            'SELECT * FROM learning_roadmaps WHERE user_id=%s ORDER BY created_at DESC LIMIT 1',
            (user_id,), one=True
        )
        
        reports_dir = os.path.join('uploads', 'reports', str(user_id))
        os.makedirs(reports_dir, exist_ok=True)
        filename = f'career_report_{uuid.uuid4().hex[:8]}.pdf'
        output_path = os.path.join(reports_dir, filename)
        
        try:
            result = generate_pdf_report(user, profile, analysis, 'Career', output_path, interview_stats=interview_stats, roadmap=roadmap)
            print(f"Result: {result}")
        except Exception as e:
            print("Exception:")
            traceback.print_exc()

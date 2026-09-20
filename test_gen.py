from app import app
from services.resume_generation_service import generate_resume
from flask import session

with app.app_context():
    try:
        generate_resume(
            user_id=1,
            wizard_data=None,
            source_resume_id=1,
            company_id=None,
            company_name_manual='',
            job_role='Software Engineer',
            job_description='',
            template='classic',
            source_resume_text='Fake resume text'
        )
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

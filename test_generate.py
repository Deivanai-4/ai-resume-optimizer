import traceback
from app import create_app
from services.resume_generation_service import generate_resume, collect_candidate_data
from models.user import UserModel
from models.profile import ProfileModel

app = create_app()
with app.app_context():
    print("Testing generate_resume with a dummy user...")
    # Create a dummy user
    try:
        from database.db import execute_db
        execute_db("INSERT INTO users (full_name, email, password_hash) VALUES ('Test Friend', 'friend@test.com', 'hash')", get_id=False)
        user = UserModel.get_by_email('friend@test.com')
        user_id = user['id']
        ProfileModel.create_default(user_id)
        print(f"Created dummy user_id = {user_id}")
        
        # Test generate_resume
        res = generate_resume(user_id=user_id, wizard_data={})
        print("Success:", res.get('label'))
    except Exception as e:
        print("EXCEPTION RAISED:")
        traceback.print_exc()
    finally:
        if 'user_id' in locals():
            execute_db("DELETE FROM student_profiles WHERE user_id=%s", (user_id,))
            execute_db("DELETE FROM users WHERE id=%s", (user_id,))

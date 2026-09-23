"""User Model — Database operations for users."""
from database.db import query_db, execute_db
from flask_bcrypt import generate_password_hash, check_password_hash

class UserModel:
    
    @staticmethod
    def get_by_id(user_id):
        return query_db('SELECT * FROM users WHERE id = %s', (user_id,), one=True)
        
    @staticmethod
    def get_by_email(email):
        return query_db('SELECT * FROM users WHERE email = %s', (email.strip().lower(),), one=True)
        
    @staticmethod
    def create(full_name, email, password):
        hashed_password = generate_password_hash(password).decode('utf-8')
        query = '''
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
        '''
        return execute_db(query, (full_name, email.strip().lower(), hashed_password), get_id=True)
        
    @staticmethod
    def check_password(user, password):
        if not user or not user.get('password_hash'):
            return False
        return check_password_hash(user['password_hash'], password)
        
    @staticmethod
    def update_password(user_id, new_password):
        hashed_password = generate_password_hash(new_password).decode('utf-8')
        execute_db('UPDATE users SET password_hash = %s WHERE id = %s', (hashed_password, user_id))
        
    @staticmethod
    def delete(user_id):
        # Cascade deletes or manual cleanup of related records if needed
        execute_db('DELETE FROM users WHERE id = %s', (user_id,))
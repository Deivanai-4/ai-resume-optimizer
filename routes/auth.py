"""Authentication Blueprint — Login, Register, Logout, Password Reset."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from utils.decorators import login_required
from utils.helpers import log_activity
from models.user import UserModel
from models.profile import ProfileModel
from database.db import query_db, execute_db
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me')
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')
            
        user = UserModel.get_by_email(email)
        
        if user and UserModel.check_password(user, password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            
            if remember:
                session.permanent = True
            
            log_activity(user['id'], 'login', 'User logged in successfully')
            flash(f'Welcome back, {user["full_name"]}! 👋', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not full_name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
            
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        existing = UserModel.get_by_email(email)
        if existing:
            flash('Email address is already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))
            
        try:
            user_id = UserModel.create(full_name, email, password)
            
            # Initialize profile and settings — if either fails, clean up the orphaned user row
            try:
                ProfileModel.create_default(user_id)
                execute_db('INSERT INTO settings (user_id) VALUES (%s)', (user_id,))
            except Exception as setup_err:
                current_app.logger.error(f"Post-user setup failed for user_id={user_id}: {setup_err}")
                execute_db('DELETE FROM users WHERE id = %s', (user_id,))
                raise
            
            session['user_id'] = user_id
            session['user_name'] = full_name
            session['user_email'] = email
            
            log_activity(user_id, 'register', 'New account created')
            flash('Account created successfully! Welcome aboard. 🚀', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            current_app.logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, 'logout', 'User logged out')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = UserModel.get_by_email(email)
        
        if user:
            token = secrets.token_hex(16)
            expires = datetime.now() + timedelta(hours=1)
            execute_db(
                'UPDATE users SET reset_token=%s, reset_expires=%s WHERE id=%s',
                (token, expires, user['id'])
            )
            # In a production app, email this link. For local dev, flash it directly:
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Password reset link generated (Dev Mode): {reset_url}', 'info')
        else:
            flash('If that email exists, a reset link has been sent.', 'info')
            
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = query_db('SELECT * FROM users WHERE reset_token=%s AND reset_expires > NOW()', (token,), one=True)
    
    if not user:
        flash('Invalid or expired password reset token.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('reset_password.html', token=token)
            
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
            
        UserModel.update_password(user['id'], password)
        execute_db('UPDATE users SET reset_token=NULL, reset_expires=NULL WHERE id=%s', (user['id'],))
        
        flash('Password updated successfully! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_password.html', token=token)
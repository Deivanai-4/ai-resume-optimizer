"""Settings Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import log_activity
from models.user import UserModel
from database.db import query_db, execute_db

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@login_required
def index():
    user_id = session['user_id']
    user = UserModel.get_by_id(user_id)
    settings = query_db('SELECT * FROM settings WHERE user_id=%s', (user_id,), one=True)
    return render_template('settings.html', user=user, settings=settings)


@settings_bp.route('/settings/update-password', methods=['POST'])
@login_required
def update_password():
    user_id = session['user_id']
    current = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    
    user = UserModel.get_by_id(user_id)
    
    if not UserModel.check_password(user, current):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.index'))
    
    if len(new_pass) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('settings.index'))
    
    if new_pass != confirm:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('settings.index'))
    
    UserModel.update_password(user_id, new_pass)
    log_activity(user_id, 'password_change', 'Password changed successfully')
    flash('Password updated successfully!', 'success')
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    user_id = session['user_id']
    theme = request.form.get('theme', 'light')
    email_notif = 1 if request.form.get('email_notifications') else 0
    placement_alerts = 1 if request.form.get('placement_alerts') else 0
    weekly_report = 1 if request.form.get('weekly_report') else 0
    
    execute_db(
        '''UPDATE settings SET theme=%s, email_notifications=%s, placement_alerts=%s,
           weekly_report=%s WHERE user_id=%s''',
        (theme, email_notif, placement_alerts, weekly_report, user_id)
    )
    log_activity(user_id, 'settings_update', 'Updated preferences')
    flash('Preferences saved!', 'success')
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    password = request.form.get('confirm_password', '')
    
    user = UserModel.get_by_id(user_id)
    if not UserModel.check_password(user, password):
        flash('Password incorrect. Account not deleted.', 'danger')
        return redirect(url_for('settings.index'))
    
    UserModel.delete(user_id)
    session.clear()
    flash('Your account has been deleted. We are sorry to see you go.', 'info')
    return redirect(url_for('auth.register'))

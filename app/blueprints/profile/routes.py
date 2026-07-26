from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db, bcrypt
from app.models import Decision, JournalEntry, ActivityLog
from . import profile_bp
from .forms import ProfileForm, PasswordForm


@profile_bp.route('/')
@login_required
def index():
    total_decisions = Decision.query.filter_by(user_id=current_user.id).count()
    completed_decisions = Decision.query.filter_by(user_id=current_user.id, status='completed').count()
    journal_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
    activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(10).all()

    return render_template('profile/index.html',
                           total_decisions=total_decisions,
                           completed_decisions=completed_decisions,
                           journal_count=journal_count,
                           activities=activities)


@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordForm()

    if request.method == 'POST':
        action = request.form.get('form_action')

        if action == 'update_profile' and profile_form.validate():
            current_user.full_name = profile_form.full_name.data.strip()
            current_user.username = profile_form.username.data.strip().lower()
            current_user.email = profile_form.email.data.strip().lower()
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('profile.settings'))

        elif action == 'update_password' and password_form.validate():
            if bcrypt.check_password_hash(current_user.password_hash, password_form.current_password.data):
                current_user.password_hash = bcrypt.generate_password_hash(password_form.new_password.data).decode('utf-8')
                db.session.commit()
                flash('Password updated successfully.', 'success')
                return redirect(url_for('profile.settings'))
            else:
                flash('Current password is incorrect.', 'danger')

    return render_template('profile/settings.html',
                           profile_form=profile_form,
                           password_form=password_form)


@profile_bp.route('/dark-mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    data = request.get_json(silent=True) or {}
    dark = data.get('dark_mode', False)
    current_user.dark_mode = bool(dark)
    db.session.commit()
    return jsonify({'dark_mode': current_user.dark_mode})

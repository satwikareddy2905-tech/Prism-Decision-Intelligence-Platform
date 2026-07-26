from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, bcrypt
from app.models import User, ActivityLog
from . import auth_bp
from .forms import LoginForm, SignupForm, ForgotPasswordForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form, title='Sign In')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = SignupForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            full_name=form.full_name.data.strip(),
            username=form.username.data.strip().lower(),
            email=form.email.data.strip().lower(),
            password_hash=hashed,
        )
        db.session.add(user)
        db.session.commit()

        # Create welcome notification
        from app.models.notification import Notification
        welcome_notif = Notification(
            user_id=user.id,
            title="Welcome to Prism!",
            message="Get started by creating your first structured decision.",
            link=url_for('decisions.new_decision')
        )
        db.session.add(welcome_notif)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to Prism, {user.display_name}!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/signup.html', form=form, title='Create Account')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = ForgotPasswordForm()
    sent = False

    if form.validate_on_submit():
        # Email sending is stubbed — UI shows confirmation regardless
        # In production: generate token, send email, store token in DB
        sent = True
        flash('If an account exists with that email, a reset link has been sent.', 'info')

    return render_template('auth/forgot_password.html', form=form, sent=sent, title='Reset Password')

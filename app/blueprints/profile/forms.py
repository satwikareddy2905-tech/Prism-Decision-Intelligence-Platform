from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from flask_login import current_user
from app.models import User


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(2, 120)])
    username = StringField('Username', validators=[DataRequired(), Length(3, 80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Save Profile')

    def validate_username(self, field):
        if field.data != current_user.username:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('Username already in use.')

    def validate_email(self, field):
        if field.data.lower() != current_user.email.lower():
            if User.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('Email already registered.')


class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Password')

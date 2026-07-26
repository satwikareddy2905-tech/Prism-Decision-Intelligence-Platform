from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField,
                     DateField, BooleanField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional


class DecisionForm(FlaskForm):
    title = StringField('Decision Title', validators=[
        DataRequired(), Length(2, 200)
    ])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('Technology', 'Technology'),
        ('Career', 'Career'),
        ('Finance', 'Finance'),
        ('Education', 'Education'),
        ('Travel', 'Travel'),
        ('Health', 'Health'),
        ('Business', 'Business'),
        ('Real Estate', 'Real Estate'),
        ('Lifestyle', 'Lifestyle'),
        ('Other', 'Other'),
    ])
    goal = StringField('Decision Goal', validators=[Optional(), Length(max=500)],
                       description='What outcome are you trying to achieve?')
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    deadline = DateField('Deadline', validators=[Optional()])
    privacy = SelectField('Privacy', choices=[
        ('private', 'Private — only you can see this'),
        ('shared', 'Shared — anyone with the link can view'),
    ], default='private')
    submit = SubmitField('Save Decision')

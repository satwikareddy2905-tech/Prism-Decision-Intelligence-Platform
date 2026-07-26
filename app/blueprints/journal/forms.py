from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class JournalEntryForm(FlaskForm):
    outcome = TextAreaField('Actual Outcome', validators=[DataRequired()],
                            description='What happened after making this decision?')
    reflection = TextAreaField('Personal Reflection', validators=[Optional()],
                               description='How do you feel about the process and result?')
    lessons_learned = TextAreaField('Lessons Learned', validators=[Optional()],
                                    description='What would you do differently next time?')
    satisfaction_score = IntegerField('Satisfaction Score (1 – 10)', validators=[
        Optional(), NumberRange(min=1, max=10)
    ], default=8)
    would_choose_again = BooleanField('I would make the exact same choice again', default=True)
    submit = SubmitField('Save Journal Entry')

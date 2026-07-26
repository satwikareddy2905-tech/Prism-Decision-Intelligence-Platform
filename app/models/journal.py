from datetime import datetime
from app.extensions import db


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decisions.id', ondelete='CASCADE'),
                             nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    outcome = db.Column(db.Text, nullable=True)
    reflection = db.Column(db.Text, nullable=True)
    lessons_learned = db.Column(db.Text, nullable=True)
    satisfaction_score = db.Column(db.Integer, nullable=True)  # 1-10
    would_choose_again = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    @property
    def satisfaction_label(self):
        if self.satisfaction_score is None:
            return 'Not rated'
        if self.satisfaction_score >= 9:
            return 'Very Satisfied'
        elif self.satisfaction_score >= 7:
            return 'Satisfied'
        elif self.satisfaction_score >= 5:
            return 'Neutral'
        elif self.satisfaction_score >= 3:
            return 'Unsatisfied'
        else:
            return 'Very Unsatisfied'

    def __repr__(self):
        return f'<JournalEntry decision={self.decision_id}>'

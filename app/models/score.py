from datetime import datetime
from app.extensions import db


class Score(db.Model):
    __tablename__ = 'scores'
    __table_args__ = (
        db.UniqueConstraint('criterion_id', 'option_id', name='uq_criterion_option'),
    )

    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decisions.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criteria.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    raw_score = db.Column(db.Float, nullable=False, default=5.0)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    @property
    def score_label(self):
        """Human-readable label for a 1-10 score."""
        if self.raw_score >= 9:
            return 'Excellent'
        elif self.raw_score >= 7:
            return 'Good'
        elif self.raw_score >= 5:
            return 'Average'
        elif self.raw_score >= 3:
            return 'Below Average'
        else:
            return 'Poor'

    @property
    def score_class(self):
        """Bootstrap/CSS class based on score."""
        if self.raw_score >= 7:
            return 'score-high'
        elif self.raw_score >= 5:
            return 'score-medium'
        else:
            return 'score-low'

    def __repr__(self):
        return f'<Score criterion={self.criterion_id} option={self.option_id} score={self.raw_score}>'

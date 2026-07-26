from datetime import datetime
from app.extensions import db


class Criterion(db.Model):
    __tablename__ = 'criteria'

    PRIORITIES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decisions.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, nullable=False, default=5.0)
    priority = db.Column(db.String(20), nullable=False, default='medium')
    is_mandatory = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scores = db.relationship('Score', backref='criterion', lazy='dynamic',
                              cascade='all, delete-orphan')

    @property
    def priority_label(self):
        return dict(self.PRIORITIES).get(self.priority, self.priority)

    @property
    def weight_percentage(self):
        """Weight as a raw value for display (1–10 scale)."""
        return round(self.weight, 1)

    def __repr__(self):
        return f'<Criterion {self.name} w={self.weight}>'

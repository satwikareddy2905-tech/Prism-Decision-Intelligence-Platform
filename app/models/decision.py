from datetime import datetime
from app.extensions import db


class Decision(db.Model):
    __tablename__ = 'decisions'

    CATEGORIES = [
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
    ]

    STATUSES = [
        ('draft', 'Draft'),
        ('active', 'In Progress'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    PRIVACY_OPTIONS = [
        ('private', 'Private'),
        ('shared', 'Shared'),
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False, default='Other')
    goal = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='draft')
    privacy = db.Column(db.String(20), nullable=False, default='private')
    deadline = db.Column(db.Date, nullable=True)
    pinned = db.Column(db.Boolean, default=False, nullable=False)
    final_choice_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='SET NULL'),
                                 nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    # Relationships
    criteria = db.relationship('Criterion', backref='decision', lazy='dynamic',
                                cascade='all, delete-orphan',
                                order_by='Criterion.sort_order')
    options = db.relationship('Option', backref='decision', lazy='dynamic',
                               cascade='all, delete-orphan',
                               foreign_keys='Option.decision_id',
                               order_by='Option.sort_order')
    scores = db.relationship('Score', backref='decision', lazy='dynamic',
                              cascade='all, delete-orphan')
    journal_entry = db.relationship('JournalEntry', backref='decision',
                                     uselist=False, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='decision', lazy='dynamic',
                                     cascade='all, delete-orphan')
    final_choice = db.relationship('Option', foreign_keys=[final_choice_id],
                                    post_update=True)

    @property
    def status_label(self):
        return dict(self.STATUSES).get(self.status, self.status)

    @property
    def category_icon(self):
        icons = {
            'Technology': 'bi-cpu',
            'Career': 'bi-briefcase',
            'Finance': 'bi-currency-dollar',
            'Education': 'bi-mortarboard',
            'Travel': 'bi-airplane',
            'Health': 'bi-heart-pulse',
            'Business': 'bi-building',
            'Real Estate': 'bi-house',
            'Lifestyle': 'bi-stars',
            'Other': 'bi-grid',
        }
        return icons.get(self.category, 'bi-grid')

    @property
    def is_overdue(self):
        from datetime import date
        return (self.deadline and self.deadline < date.today()
                and self.status not in ('completed', 'archived'))

    @property
    def criteria_count(self):
        return self.criteria.count()

    @property
    def options_count(self):
        return self.options.count()

    @property
    def is_ready_to_compare(self):
        """True when criteria, options, and at least some scores exist."""
        return self.criteria_count >= 1 and self.options_count >= 2

    def touch(self):
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f'<Decision {self.title}>'

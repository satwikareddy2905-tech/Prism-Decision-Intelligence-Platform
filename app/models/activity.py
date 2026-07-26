from datetime import datetime
from app.extensions import db


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    ACTIONS = {
        'created_decision': 'Created decision',
        'updated_decision': 'Updated decision',
        'added_criterion': 'Added criterion',
        'removed_criterion': 'Removed criterion',
        'added_option': 'Added option',
        'removed_option': 'Removed option',
        'scored_option': 'Scored options',
        'completed_decision': 'Marked as complete',
        'archived_decision': 'Archived decision',
        'pinned_decision': 'Pinned decision',
        'unpinned_decision': 'Unpinned decision',
        'added_journal': 'Added journal entry',
        'updated_journal': 'Updated journal entry',
        'duplicated_decision': 'Duplicated decision',
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decisions.id', ondelete='CASCADE'),
                             nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def action_label(self):
        return self.ACTIONS.get(self.action, self.action)

    @property
    def time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            m = seconds // 60
            return f'{m} minute{"s" if m != 1 else ""} ago'
        elif seconds < 86400:
            h = seconds // 3600
            return f'{h} hour{"s" if h != 1 else ""} ago'
        elif seconds < 604800:
            d = seconds // 86400
            return f'{d} day{"s" if d != 1 else ""} ago'
        else:
            return self.created_at.strftime('%b %d, %Y')

    def __repr__(self):
        return f'<ActivityLog {self.action}>'

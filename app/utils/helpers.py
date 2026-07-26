from datetime import datetime
from markupsafe import Markup


def register_template_filters(app):
    @app.template_filter('dateformat')
    def dateformat(value, fmt='%b %d, %Y'):
        if value is None:
            return '—'
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(fmt)

    @app.template_filter('timeago')
    def timeago(value):
        if value is None:
            return '—'
        now = datetime.utcnow()
        diff = now - value
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            m = seconds // 60
            return f'{m}m ago'
        elif seconds < 86400:
            h = seconds // 3600
            return f'{h}h ago'
        elif seconds < 604800:
            d = seconds // 86400
            return f'{d}d ago'
        return value.strftime('%b %d')

    @app.template_filter('currency')
    def currency(value):
        if value is None:
            return '—'
        return f'${float(value):,.2f}'

    @app.template_filter('score_class')
    def score_class_filter(value):
        if value is None:
            return 'score-empty'
        v = float(value)
        if v >= 7:
            return 'score-high'
        elif v >= 5:
            return 'score-medium'
        else:
            return 'score-low'

    @app.template_filter('pct')
    def pct(value, decimals=1):
        if value is None:
            return '—'
        return f'{float(value):.{decimals}f}%'

    @app.template_filter('truncate_smart')
    def truncate_smart(value, length=80):
        if not value:
            return ''
        if len(value) <= length:
            return value
        return value[:length].rsplit(' ', 1)[0] + '…'

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models.notification import Notification
        
        unread_notifications = []
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_notifications = (Notification.query
                                       .filter_by(user_id=current_user.id, is_read=False)
                                       .order_by(Notification.created_at.desc())
                                       .limit(5).all())
                unread_count = (Notification.query
                                .filter_by(user_id=current_user.id, is_read=False)
                                .count())
            except Exception:
                pass

        return {
            'now': datetime.utcnow(),
            'unread_notifications': unread_notifications,
            'unread_count': unread_count,
        }

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Decision, ActivityLog
from . import dashboard_bp


@dashboard_bp.route('/')
@login_required
def index():
    user_id = current_user.id

    # Check for overdue deadlines
    from datetime import date
    from app.models.notification import Notification
    from flask import url_for
    from app.extensions import db
    overdue_decisions = (Decision.query
                         .filter_by(user_id=user_id)
                         .filter(Decision.deadline < date.today())
                         .filter(Decision.status.notin_(['completed', 'archived']))
                         .all())
    for dec in overdue_decisions:
        link_url = url_for('decisions.detail', decision_id=dec.id)
        notif_exists = Notification.query.filter_by(
            user_id=user_id,
            link=link_url,
            title="Decision Overdue"
        ).first()
        if not notif_exists:
            notif = Notification(
                user_id=user_id,
                title="Decision Overdue",
                message=f"The deadline for '{dec.title}' has passed.",
                link=link_url
            )
            db.session.add(notif)
    db.session.commit()

    # Pinned decisions (up to 4)
    pinned = (Decision.query
              .filter_by(user_id=user_id, pinned=True)
              .filter(Decision.status.notin_(['archived']))
              .order_by(Decision.updated_at.desc())
              .limit(4).all())

    # Active / in-progress
    active = (Decision.query
              .filter_by(user_id=user_id, status='active')
              .order_by(Decision.updated_at.desc())
              .limit(6).all())

    # Recently completed
    completed = (Decision.query
                 .filter_by(user_id=user_id, status='completed')
                 .order_by(Decision.updated_at.desc())
                 .limit(4).all())

    # Drafts
    drafts = (Decision.query
              .filter_by(user_id=user_id, status='draft')
              .order_by(Decision.updated_at.desc())
              .limit(4).all())

    # Recent activity (last 10)
    recent_activity = (ActivityLog.query
                       .filter_by(user_id=user_id)
                       .order_by(ActivityLog.created_at.desc())
                       .limit(10).all())

    # Stats
    total_decisions = Decision.query.filter_by(user_id=user_id).count()
    completed_count = Decision.query.filter_by(user_id=user_id, status='completed').count()
    active_count = Decision.query.filter_by(user_id=user_id, status='active').count()
    draft_count = Decision.query.filter_by(user_id=user_id, status='draft').count()

    # Overdue
    from datetime import date
    overdue = (Decision.query
               .filter_by(user_id=user_id)
               .filter(Decision.deadline < date.today())
               .filter(Decision.status.notin_(['completed', 'archived']))
               .count())

    return render_template('dashboard/index.html',
                           pinned=pinned,
                           active=active,
                           completed=completed,
                           drafts=drafts,
                           recent_activity=recent_activity,
                           total_decisions=total_decisions,
                           completed_count=completed_count,
                           active_count=active_count,
                           draft_count=draft_count,
                           overdue=overdue)

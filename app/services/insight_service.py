"""
Insight Service — analyzes a user's historical decisions to
surface meaningful patterns. All values computed from real DB data.
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Decision, Criterion, Score, JournalEntry


def get_personal_insights(user_id):
    """Returns a dict of insight data for a user's analytics page."""

    # -- Base queries --
    decisions = Decision.query.filter_by(user_id=user_id).all()
    completed = [d for d in decisions if d.status == 'completed']
    total = len(decisions)

    if total == 0:
        return {'empty': True}

    # -- Category distribution --
    category_counts = {}
    for d in decisions:
        category_counts[d.category] = category_counts.get(d.category, 0) + 1

    favorite_category = max(category_counts, key=category_counts.get) if category_counts else None

    # -- Completion rate --
    completion_rate = round(len(completed) / total * 100, 1) if total > 0 else 0

    # -- Average decision time (created → updated for completed) --
    decision_times = []
    for d in completed:
        delta = d.updated_at - d.created_at
        decision_times.append(delta.total_seconds() / 3600)  # hours
    avg_decision_hours = round(sum(decision_times) / len(decision_times), 1) if decision_times else None

    # -- Monthly decisions (last 6 months) --
    monthly_data = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        count = sum(1 for d in decisions
                    if month_start <= d.created_at < month_end)
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': count,
        })

    # -- Most used criteria names --
    criteria_rows = (
        db.session.query(Criterion.name, func.count(Criterion.id).label('cnt'))
        .join(Decision, Decision.id == Criterion.decision_id)
        .filter(Decision.user_id == user_id)
        .group_by(Criterion.name)
        .order_by(func.count(Criterion.id).desc())
        .limit(8)
        .all()
    )
    top_criteria = [{'name': r.name, 'count': r.cnt} for r in criteria_rows]

    # -- Satisfaction trend from journal --
    journal_entries = (
        JournalEntry.query
        .filter_by(user_id=user_id)
        .filter(JournalEntry.satisfaction_score.isnot(None))
        .order_by(JournalEntry.created_at.asc())
        .all()
    )
    satisfaction_trend = [
        {
            'date': j.created_at.strftime('%b %Y'),
            'score': j.satisfaction_score,
            'decision': j.decision.title if j.decision else '',
        }
        for j in journal_entries
    ]

    avg_satisfaction = (
        round(sum(j['score'] for j in satisfaction_trend) / len(satisfaction_trend), 1)
        if satisfaction_trend else None
    )

    # -- Would choose again rate --
    journal_with_choice = [j for j in journal_entries if j.would_choose_again is not None]
    would_choose_again_rate = None
    if journal_with_choice:
        yes_count = sum(1 for j in journal_with_choice if j.would_choose_again)
        would_choose_again_rate = round(yes_count / len(journal_with_choice) * 100, 1)

    return {
        'empty': False,
        'total_decisions': total,
        'completed_decisions': len(completed),
        'active_decisions': sum(1 for d in decisions if d.status == 'active'),
        'draft_decisions': sum(1 for d in decisions if d.status == 'draft'),
        'completion_rate': completion_rate,
        'favorite_category': favorite_category,
        'category_distribution': category_counts,
        'monthly_decisions': monthly_data,
        'avg_decision_hours': avg_decision_hours,
        'top_criteria': top_criteria,
        'satisfaction_trend': satisfaction_trend,
        'avg_satisfaction': avg_satisfaction,
        'would_choose_again_rate': would_choose_again_rate,
        'pinned_count': sum(1 for d in decisions if d.pinned),
    }

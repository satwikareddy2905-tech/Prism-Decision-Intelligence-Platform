from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Decision, Criterion, Option, JournalEntry
from app.extensions import db
from . import search_bp


@search_bp.route('/')
@login_required
def index():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('search/results.html', query='', results=None)

    term = f'%{query}%'

    # Search decisions
    decisions = (Decision.query
                 .filter_by(user_id=current_user.id)
                 .filter(
                     (Decision.title.ilike(term)) |
                     (Decision.goal.ilike(term)) |
                     (Decision.description.ilike(term)) |
                     (Decision.category.ilike(term))
                 ).all())

    # Search criteria
    criteria = (Criterion.query
                .join(Decision)
                .filter(Decision.user_id == current_user.id)
                .filter(
                    (Criterion.name.ilike(term)) |
                    (Criterion.description.ilike(term))
                ).all())

    # Search options
    options = (Option.query
               .join(Decision, Option.decision_id == Decision.id)
               .filter(Decision.user_id == current_user.id)
               .filter(
                   (Option.name.ilike(term)) |
                   (Option.description.ilike(term)) |
                   (Option.notes.ilike(term))
               ).all())

    # Search journal entries
    journal_entries = (JournalEntry.query
                       .filter_by(user_id=current_user.id)
                       .filter(
                           (JournalEntry.outcome.ilike(term)) |
                           (JournalEntry.reflection.ilike(term)) |
                           (JournalEntry.lessons_learned.ilike(term))
                       ).all())

    results = {
        'decisions': decisions,
        'criteria': criteria,
        'options': options,
        'journal_entries': journal_entries,
        'total_count': len(decisions) + len(criteria) + len(options) + len(journal_entries)
    }

    return render_template('search/results.html', query=query, results=results)

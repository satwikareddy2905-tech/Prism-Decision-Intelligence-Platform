"""
API Blueprint — AJAX endpoints for criteria, options, scores.
All endpoints return JSON. CSRF enforced via X-CSRFToken header.
"""

from flask import request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Decision, Criterion, Option, Score, ActivityLog, CustomAttribute
from app.services.scoring_service import upsert_score, calculate_results
from . import api_bp


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _get_decision(decision_id):
    """Get decision belonging to current user or 403."""
    d = Decision.query.filter_by(id=decision_id, user_id=current_user.id).first()
    if not d:
        abort(403)
    return d


def _log(decision_id, action, description=''):
    log = ActivityLog(
        user_id=current_user.id,
        decision_id=decision_id,
        action=action,
        description=description,
    )
    db.session.add(log)


def _results_payload(decision):
    """Compact results payload for live recalculation response."""
    results = calculate_results(decision)
    if not results:
        return None
    return {
        'results': [
            {
                'option_id': r['option'].id,
                'option_name': r['option'].name,
                'normalized_score': r['normalized_score'],
                'rank': r['rank'],
                'has_disqualifier': r['has_disqualifier'],
                'coverage': r['coverage'],
            }
            for r in results['results']
        ]
    }


# ==========================================================================
# CRITERIA
# ==========================================================================

@api_bp.route('/decisions/<int:decision_id>/criteria', methods=['POST'])
@login_required
def add_criterion(decision_id):
    decision = _get_decision(decision_id)
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Criterion name is required.'}), 400
    if len(name) > 200:
        return jsonify({'error': 'Name too long (max 200 chars).'}), 400

    # Next sort order
    max_order = db.session.query(
        db.func.max(Criterion.sort_order)
    ).filter_by(decision_id=decision_id).scalar() or 0

    criterion = Criterion(
        decision_id=decision_id,
        name=name,
        description=(data.get('description') or '').strip() or None,
        weight=min(max(float(data.get('weight', 5)), 0.1), 10),
        priority=data.get('priority', 'medium') if data.get('priority') in
                 ['low', 'medium', 'high', 'critical'] else 'medium',
        is_mandatory=bool(data.get('is_mandatory', False)),
        sort_order=max_order + 1,
    )
    db.session.add(criterion)
    decision.touch()
    _log(decision_id, 'added_criterion', f'Added criterion "{name}"')
    db.session.commit()

    return jsonify({
        'id': criterion.id,
        'name': criterion.name,
        'description': criterion.description,
        'weight': criterion.weight,
        'priority': criterion.priority,
        'is_mandatory': criterion.is_mandatory,
        'sort_order': criterion.sort_order,
        'priority_label': criterion.priority_label,
    }), 201


@api_bp.route('/criteria/<int:criterion_id>', methods=['PUT'])
@login_required
def update_criterion(criterion_id):
    criterion = Criterion.query.get_or_404(criterion_id)
    # Verify ownership
    decision = Decision.query.filter_by(
        id=criterion.decision_id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty.'}), 400
        criterion.name = name

    if 'description' in data:
        criterion.description = data['description'].strip() or None
    if 'weight' in data:
        criterion.weight = min(max(float(data['weight']), 0.1), 10)
    if 'priority' in data and data['priority'] in ['low', 'medium', 'high', 'critical']:
        criterion.priority = data['priority']
    if 'is_mandatory' in data:
        criterion.is_mandatory = bool(data['is_mandatory'])

    decision.touch()
    db.session.commit()

    return jsonify({
        'id': criterion.id,
        'name': criterion.name,
        'weight': criterion.weight,
        'priority': criterion.priority,
        'is_mandatory': criterion.is_mandatory,
        'priority_label': criterion.priority_label,
    })


@api_bp.route('/criteria/<int:criterion_id>', methods=['DELETE'])
@login_required
def delete_criterion(criterion_id):
    criterion = Criterion.query.get_or_404(criterion_id)
    decision = Decision.query.filter_by(
        id=criterion.decision_id, user_id=current_user.id
    ).first_or_404()

    name = criterion.name
    db.session.delete(criterion)
    decision.touch()
    _log(decision.id, 'removed_criterion', f'Removed criterion "{name}"')
    db.session.commit()

    return jsonify({'message': f'Criterion "{name}" deleted.'})


@api_bp.route('/decisions/<int:decision_id>/criteria/reorder', methods=['POST'])
@login_required
def reorder_criteria(decision_id):
    decision = _get_decision(decision_id)
    data = request.get_json(silent=True) or {}
    order = data.get('order', [])  # list of criterion IDs in new order

    for idx, crit_id in enumerate(order):
        Criterion.query.filter_by(
            id=crit_id, decision_id=decision_id
        ).update({'sort_order': idx})

    decision.touch()
    db.session.commit()
    return jsonify({'message': 'Reordered.'})


# ==========================================================================
# OPTIONS
# ==========================================================================

@api_bp.route('/decisions/<int:decision_id>/options', methods=['POST'])
@login_required
def add_option(decision_id):
    decision = _get_decision(decision_id)
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Option name is required.'}), 400

    max_order = db.session.query(
        db.func.max(Option.sort_order)
    ).filter_by(decision_id=decision_id).scalar() or 0

    price = None
    if data.get('price'):
        try:
            price = float(data['price'])
        except (ValueError, TypeError):
            price = None

    option = Option(
        decision_id=decision_id,
        name=name,
        description=(data.get('description') or '').strip() or None,
        price=price,
        url=(data.get('url') or '').strip() or None,
        notes=(data.get('notes') or '').strip() or None,
        sort_order=max_order + 1,
    )
    db.session.add(option)
    decision.touch()
    db.session.flush()

    # Handle custom attributes
    if 'attributes' in data and isinstance(data['attributes'], list):
        for attr in data['attributes']:
            k = (attr.get('key') or '').strip()
            v = (attr.get('value') or '').strip()
            if k:
                db.session.add(CustomAttribute(
                    option_id=option.id, attr_key=k, attr_value=v
                ))

    _log(decision_id, 'added_option', f'Added option "{name}"')
    db.session.commit()

    # Create empty score records for all existing criteria
    criteria = decision.criteria.all()
    for c in criteria:
        existing = Score.query.filter_by(
            criterion_id=c.id, option_id=option.id
        ).first()
        if not existing:
            score = Score(
                decision_id=decision_id,
                criterion_id=c.id,
                option_id=option.id,
                raw_score=5.0,
            )
            db.session.add(score)
    db.session.commit()

    return jsonify({
        'id': option.id,
        'name': option.name,
        'description': option.description,
        'price': float(option.price) if option.price else None,
        'formatted_price': option.formatted_price,
        'url': option.url,
        'notes': option.notes,
        'sort_order': option.sort_order,
    }), 201


@api_bp.route('/options/<int:option_id>', methods=['PUT'])
@login_required
def update_option(option_id):
    option = Option.query.get_or_404(option_id)
    Decision.query.filter_by(
        id=option.decision_id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty.'}), 400
        option.name = name
    if 'description' in data:
        option.description = data['description'].strip() or None
    if 'price' in data:
        try:
            option.price = float(data['price']) if data['price'] else None
        except (ValueError, TypeError):
            pass
    if 'url' in data:
        option.url = data['url'].strip() or None
    if 'notes' in data:
        option.notes = data['notes'].strip() or None

    # Handle custom attributes
    if 'attributes' in data and isinstance(data['attributes'], list):
        # Clear existing
        CustomAttribute.query.filter_by(option_id=option.id).delete()
        for attr in data['attributes']:
            k = (attr.get('key') or '').strip()
            v = (attr.get('value') or '').strip()
            if k:
                db.session.add(CustomAttribute(
                    option_id=option.id, attr_key=k, attr_value=v
                ))

    db.session.commit()
    return jsonify({
        'id': option.id,
        'name': option.name,
        'formatted_price': option.formatted_price,
    })


@api_bp.route('/options/<int:option_id>', methods=['DELETE'])
@login_required
def delete_option(option_id):
    option = Option.query.get_or_404(option_id)
    decision = Decision.query.filter_by(
        id=option.decision_id, user_id=current_user.id
    ).first_or_404()

    name = option.name
    db.session.delete(option)
    decision.touch()
    _log(decision.id, 'removed_option', f'Removed option "{name}"')
    db.session.commit()

    return jsonify({'message': f'Option "{name}" deleted.'})


# ==========================================================================
# SCORES
# ==========================================================================

@api_bp.route('/decisions/<int:decision_id>/scores', methods=['POST'])
@login_required
def save_score(decision_id):
    decision = _get_decision(decision_id)
    data = request.get_json(silent=True) or {}

    criterion_id = data.get('criterion_id')
    option_id = data.get('option_id')
    raw_score = data.get('raw_score')
    notes = data.get('notes', '')

    if not criterion_id or not option_id:
        return jsonify({'error': 'criterion_id and option_id are required.'}), 400

    try:
        raw_score = float(raw_score)
        if not (1 <= raw_score <= 10):
            return jsonify({'error': 'Score must be between 1 and 10.'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid score value.'}), 400

    # Verify both belong to this decision
    c = Criterion.query.filter_by(id=criterion_id, decision_id=decision_id).first()
    o = Option.query.filter_by(id=option_id, decision_id=decision_id).first()
    if not c or not o:
        return jsonify({'error': 'Invalid criterion or option.'}), 400

    score = upsert_score(decision_id, criterion_id, option_id, raw_score, notes)
    decision.touch()
    _log(decision_id, 'scored_option', f'Updated score for {o.name}')

    # Return updated ranking
    payload = _results_payload(decision)

    return jsonify({
        'score_id': score.id,
        'raw_score': score.raw_score,
        'score_class': score.score_class,
        'results': payload,
    })


@api_bp.route('/decisions/<int:decision_id>/scores/bulk', methods=['POST'])
@login_required
def save_scores_bulk(decision_id):
    """Save multiple scores in one request (used by comparison matrix save-all)."""
    decision = _get_decision(decision_id)
    data = request.get_json(silent=True) or {}
    scores_data = data.get('scores', [])

    for item in scores_data:
        try:
            raw = float(item['raw_score'])
            if not (1 <= raw <= 10):
                continue
            c = Criterion.query.filter_by(
                id=item['criterion_id'], decision_id=decision_id
            ).first()
            o = Option.query.filter_by(
                id=item['option_id'], decision_id=decision_id
            ).first()
            if c and o:
                upsert_score(decision_id, item['criterion_id'],
                             item['option_id'], raw, item.get('notes', ''))
        except (KeyError, TypeError, ValueError):
            continue

    decision.touch()
    _log(decision_id, 'scored_option', 'Bulk score update')
    db.session.commit()

    payload = _results_payload(decision)
    return jsonify({'results': payload, 'message': 'Scores saved.'})


@api_bp.route('/decisions/<int:decision_id>/recalculate', methods=['POST'])
@login_required
def recalculate(decision_id):
    decision = _get_decision(decision_id)
    payload = _results_payload(decision)
    return jsonify({'results': payload})


@api_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def read_notification(notif_id):
    from app.models.notification import Notification
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read.'})


@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def read_all_notifications():
    from app.models.notification import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read.'})

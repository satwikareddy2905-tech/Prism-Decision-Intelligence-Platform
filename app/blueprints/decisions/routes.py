from flask import (render_template, redirect, url_for, flash,
                   request, abort, jsonify)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Decision, Criterion, Option, Score, ActivityLog
from app.services.scoring_service import calculate_results
from . import decisions_bp
from .forms import DecisionForm


def _log(decision_id, action, description=''):
    log = ActivityLog(
        user_id=current_user.id,
        decision_id=decision_id,
        action=action,
        description=description,
    )
    db.session.add(log)


def _get_decision_or_404(decision_id):
    decision = Decision.query.filter_by(
        id=decision_id, user_id=current_user.id
    ).first_or_404()
    return decision


# ---------------------------------------------------------------------------
# Decision List
# ---------------------------------------------------------------------------
@decisions_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    sort = request.args.get('sort', 'updated')

    q = Decision.query.filter_by(user_id=current_user.id)

    if status_filter:
        q = q.filter(Decision.status == status_filter)
    if category_filter:
        q = q.filter(Decision.category == category_filter)

    if sort == 'title':
        q = q.order_by(Decision.title.asc())
    elif sort == 'created':
        q = q.order_by(Decision.created_at.desc())
    else:  # updated
        q = q.order_by(Decision.updated_at.desc())

    decisions = q.all()

    # Category list for filter dropdown
    from sqlalchemy import func
    categories = (db.session.query(Decision.category, func.count(Decision.id))
                  .filter_by(user_id=current_user.id)
                  .group_by(Decision.category)
                  .all())

    return render_template('decisions/index.html',
                           decisions=decisions,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           sort=sort,
                           categories=categories,
                           statuses=Decision.STATUSES)


# ---------------------------------------------------------------------------
# Create Decision
# ---------------------------------------------------------------------------
@decisions_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_decision():
    form = DecisionForm()
    if form.validate_on_submit():
        decision = Decision(
            user_id=current_user.id,
            title=form.title.data.strip(),
            category=form.category.data,
            goal=form.goal.data.strip() if form.goal.data else None,
            description=form.description.data.strip() if form.description.data else None,
            deadline=form.deadline.data,
            privacy=form.privacy.data,
            status='draft',
        )
        db.session.add(decision)
        db.session.flush()  # get id before commit
        _log(decision.id, 'created_decision', f'Created "{decision.title}"')
        db.session.commit()

        flash(f'Decision "{decision.title}" created. Now add your criteria.', 'success')
        return redirect(url_for('decisions.criteria_builder', decision_id=decision.id))

    return render_template('decisions/new.html', form=form, title='New Decision')


# ---------------------------------------------------------------------------
# Decision Workspace (detail view)
# ---------------------------------------------------------------------------
@decisions_bp.route('/<int:decision_id>')
@login_required
def detail(decision_id):
    decision = _get_decision_or_404(decision_id)
    results = calculate_results(decision)
    recent_activity = (ActivityLog.query
                       .filter_by(decision_id=decision_id)
                       .order_by(ActivityLog.created_at.desc())
                       .limit(8).all())

    return render_template('decisions/detail.html',
                           decision=decision,
                           results=results,
                           recent_activity=recent_activity)


# ---------------------------------------------------------------------------
# Edit Decision Metadata
# ---------------------------------------------------------------------------
@decisions_bp.route('/<int:decision_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_decision(decision_id):
    decision = _get_decision_or_404(decision_id)
    form = DecisionForm(obj=decision)

    if form.validate_on_submit():
        form.populate_obj(decision)
        decision.touch()
        _log(decision_id, 'updated_decision', f'Updated "{decision.title}"')
        db.session.commit()
        flash('Decision updated.', 'success')
        return redirect(url_for('decisions.detail', decision_id=decision_id))

    return render_template('decisions/edit.html', form=form, decision=decision)


# ---------------------------------------------------------------------------
# Criteria Builder
# ---------------------------------------------------------------------------
@decisions_bp.route('/<int:decision_id>/criteria')
@login_required
def criteria_builder(decision_id):
    decision = _get_decision_or_404(decision_id)
    criteria = decision.criteria.order_by(Criterion.sort_order).all()
    total_weight = sum(c.weight for c in criteria)

    return render_template('decisions/criteria.html',
                           decision=decision,
                           criteria=criteria,
                           total_weight=total_weight)


# ---------------------------------------------------------------------------
# Options Builder
# ---------------------------------------------------------------------------
@decisions_bp.route('/<int:decision_id>/options')
@login_required
def options_builder(decision_id):
    decision = _get_decision_or_404(decision_id)
    options = decision.options.order_by(Option.sort_order).all()

    return render_template('decisions/options.html',
                           decision=decision,
                           options=options)


# ---------------------------------------------------------------------------
# Actions: Pin, Archive, Duplicate, Complete, Delete
# ---------------------------------------------------------------------------
@decisions_bp.route('/<int:decision_id>/pin', methods=['POST'])
@login_required
def toggle_pin(decision_id):
    decision = _get_decision_or_404(decision_id)
    decision.pinned = not decision.pinned
    action = 'pinned_decision' if decision.pinned else 'unpinned_decision'
    _log(decision_id, action)
    db.session.commit()

    label = 'pinned' if decision.pinned else 'unpinned'
    flash(f'Decision {label}.', 'success')
    return redirect(request.referrer or url_for('decisions.index'))


@decisions_bp.route('/<int:decision_id>/archive', methods=['POST'])
@login_required
def archive(decision_id):
    decision = _get_decision_or_404(decision_id)
    decision.status = 'archived'
    decision.touch()
    _log(decision_id, 'archived_decision', f'Archived "{decision.title}"')
    db.session.commit()
    flash('Decision archived.', 'success')
    return redirect(url_for('decisions.index'))


@decisions_bp.route('/<int:decision_id>/complete', methods=['POST'])
@login_required
def complete(decision_id):
    decision = _get_decision_or_404(decision_id)
    final_choice_id = request.form.get('final_choice_id', type=int)
    confidence = request.form.get('confidence', type=float)

    decision.status = 'completed'
    if final_choice_id:
        # Verify option belongs to this decision
        opt = Option.query.filter_by(id=final_choice_id,
                                      decision_id=decision_id).first()
        if opt:
            decision.final_choice_id = opt.id
    if confidence and 0 <= confidence <= 100:
        decision.confidence_score = confidence

    decision.touch()
    _log(decision_id, 'completed_decision', f'Completed "{decision.title}"')
    db.session.commit()

    # Create notification to write journal
    from app.models.notification import Notification
    notif_exists = Notification.query.filter_by(
        user_id=current_user.id,
        link=url_for('journal.new_entry', decision_id=decision.id),
        title="Share your reflection"
    ).first()
    if not notif_exists:
        notif = Notification(
            user_id=current_user.id,
            title="Share your reflection",
            message=f"You completed '{decision.title}'. Write a journal entry to record your reflection and satisfaction.",
            link=url_for('journal.new_entry', decision_id=decision.id)
        )
        db.session.add(notif)
        db.session.commit()

    flash('Decision marked as complete. Consider adding a journal entry.', 'success')
    return redirect(url_for('journal.new_entry', decision_id=decision_id))


@decisions_bp.route('/<int:decision_id>/duplicate', methods=['POST'])
@login_required
def duplicate(decision_id):
    original = _get_decision_or_404(decision_id)

    # Clone decision
    new_d = Decision(
        user_id=current_user.id,
        title=f'Copy of {original.title}',
        category=original.category,
        goal=original.goal,
        description=original.description,
        privacy=original.privacy,
        status='draft',
    )
    db.session.add(new_d)
    db.session.flush()

    # Clone criteria
    crit_map = {}
    for c in original.criteria.all():
        new_c = Criterion(
            decision_id=new_d.id,
            name=c.name,
            description=c.description,
            weight=c.weight,
            priority=c.priority,
            is_mandatory=c.is_mandatory,
            sort_order=c.sort_order,
        )
        db.session.add(new_c)
        db.session.flush()
        crit_map[c.id] = new_c.id

    # Clone options
    opt_map = {}
    for o in original.options.all():
        new_o = Option(
            decision_id=new_d.id,
            name=o.name,
            description=o.description,
            price=o.price,
            url=o.url,
            notes=o.notes,
            sort_order=o.sort_order,
        )
        db.session.add(new_o)
        db.session.flush()
        opt_map[o.id] = new_o.id

    # Clone scores
    for s in original.scores.all():
        new_crit_id = crit_map.get(s.criterion_id)
        new_opt_id = opt_map.get(s.option_id)
        if new_crit_id and new_opt_id:
            new_s = Score(
                decision_id=new_d.id,
                criterion_id=new_crit_id,
                option_id=new_opt_id,
                raw_score=s.raw_score,
                notes=s.notes,
            )
            db.session.add(new_s)

    _log(new_d.id, 'duplicated_decision', f'Duplicated from "{original.title}"')
    db.session.commit()

    flash(f'Decision duplicated as "{new_d.title}".', 'success')
    return redirect(url_for('decisions.detail', decision_id=new_d.id))


@decisions_bp.route('/<int:decision_id>/delete', methods=['POST'])
@login_required
def delete(decision_id):
    decision = _get_decision_or_404(decision_id)
    title = decision.title
    db.session.delete(decision)
    db.session.commit()
    flash(f'"{title}" has been deleted.', 'success')
    return redirect(url_for('decisions.index'))

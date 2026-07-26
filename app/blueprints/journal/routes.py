from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Decision, JournalEntry, ActivityLog
from . import journal_bp
from .forms import JournalEntryForm


@journal_bp.route('/')
@login_required
def index():
    entries = (JournalEntry.query
               .filter_by(user_id=current_user.id)
               .order_by(JournalEntry.created_at.desc())
               .all())

    completed_decisions_without_journal = (
        Decision.query
        .filter_by(user_id=current_user.id, status='completed')
        .outerjoin(JournalEntry)
        .filter(JournalEntry.id.is_(None))
        .all()
    )

    return render_template('journal/index.html',
                           entries=entries,
                           unwritten=completed_decisions_without_journal)


@journal_bp.route('/new/<int:decision_id>', methods=['GET', 'POST'])
@login_required
def new_entry(decision_id):
    decision = Decision.query.filter_by(
        id=decision_id, user_id=current_user.id
    ).first_or_404()

    if decision.journal_entry:
        flash('A journal entry already exists for this decision.', 'info')
        return redirect(url_for('journal.detail', entry_id=decision.journal_entry.id))

    form = JournalEntryForm()
    if form.validate_on_submit():
        entry = JournalEntry(
            decision_id=decision.id,
            user_id=current_user.id,
            outcome=form.outcome.data.strip(),
            reflection=form.reflection.data.strip() if form.reflection.data else None,
            lessons_learned=form.lessons_learned.data.strip() if form.lessons_learned.data else None,
            satisfaction_score=form.satisfaction_score.data,
            would_choose_again=form.would_choose_again.data,
        )
        db.session.add(entry)
        log = ActivityLog(
            user_id=current_user.id,
            decision_id=decision.id,
            action='added_journal',
            description=f'Added journal entry for "{decision.title}"'
        )
        db.session.add(log)
        db.session.commit()

        flash('Journal entry created.', 'success')
        return redirect(url_for('journal.detail', entry_id=entry.id))

    return render_template('journal/new.html', form=form, decision=decision)


@journal_bp.route('/<int:entry_id>')
@login_required
def detail(entry_id):
    entry = JournalEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()

    return render_template('journal/detail.html', entry=entry)


@journal_bp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()

    form = JournalEntryForm(obj=entry)
    if form.validate_on_submit():
        form.populate_obj(entry)
        log = ActivityLog(
            user_id=current_user.id,
            decision_id=entry.decision_id,
            action='updated_journal',
            description=f'Updated journal entry for "{entry.decision.title}"'
        )
        db.session.add(log)
        db.session.commit()

        flash('Journal entry updated.', 'success')
        return redirect(url_for('journal.detail', entry_id=entry.id))

    return render_template('journal/edit.html', form=form, entry=entry)

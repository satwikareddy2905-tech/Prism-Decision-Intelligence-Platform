from flask import render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Decision
from app.services.report_service import generate_excel_report, generate_pdf_report
from . import reports_bp


@reports_bp.route('/')
@login_required
def index():
    decisions = (Decision.query
                 .filter_by(user_id=current_user.id)
                 .order_by(Decision.updated_at.desc())
                 .all())
    return render_template('reports/index.html', decisions=decisions)


@reports_bp.route('/excel/<int:decision_id>')
@login_required
def download_excel(decision_id):
    decision = Decision.query.filter_by(
        id=decision_id, user_id=current_user.id
    ).first_or_404()

    stream = generate_excel_report(decision)
    filename = f"Prism_Report_{decision.title.replace(' ', '_')}.xlsx"

    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@reports_bp.route('/pdf/<int:decision_id>')
@login_required
def download_pdf(decision_id):
    decision = Decision.query.filter_by(
        id=decision_id, user_id=current_user.id
    ).first_or_404()

    stream = generate_pdf_report(decision)
    if not stream:
        flash('Failed to render PDF report.', 'danger')
        return redirect(url_for('reports.index'))

    filename = f"Prism_Report_{decision.title.replace(' ', '_')}.pdf"
    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

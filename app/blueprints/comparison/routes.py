from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Decision
from app.services.scoring_service import calculate_results, get_score_matrix
from app.services.ai_service import generate_comparison_summary
from . import comparison_bp


@comparison_bp.route('/<int:decision_id>/compare')
@login_required
def compare_view(decision_id):
    decision = Decision.query.filter_by(
        id=decision_id, user_id=current_user.id
    ).first_or_404()

    results = calculate_results(decision)
    matrix = get_score_matrix(decision)
    ai_analysis = generate_comparison_summary(decision)

    return render_template('comparison/index.html',
                           decision=decision,
                           results=results,
                           matrix=matrix,
                           ai_analysis=ai_analysis)

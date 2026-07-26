from flask import render_template, jsonify
from flask_login import login_required, current_user
from app.services.insight_service import get_personal_insights
from . import analytics_bp


@analytics_bp.route('/')
@login_required
def index():
    insights = get_personal_insights(current_user.id)
    return render_template('analytics/index.html', insights=insights)


@analytics_bp.route('/api/data')
@login_required
def get_chart_data():
    insights = get_personal_insights(current_user.id)
    return jsonify(insights)

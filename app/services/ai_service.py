"""
Rule-based AI service — generates human-readable summaries
strictly from comparison data. No external API required.
"""

from app.services.scoring_service import calculate_results


def generate_comparison_summary(decision):
    """
    Generates a structured analysis dict from scoring data.
    Returns None if insufficient data.
    """
    data = calculate_results(decision)
    if not data or len(data['results']) < 2:
        return None

    results = data['results']
    criteria = data['criteria']
    recommendation = data['recommendation']
    runner_up = data['runner_up']

    rec_option = recommendation['option']
    runner_option = runner_up['option']

    # --- Identify strengths and weaknesses per option ---
    def get_strengths_weaknesses(result):
        strengths = []
        weaknesses = []
        for cs in result['criterion_scores']:
            if cs['raw_score'] is None:
                continue
            if cs['raw_score'] >= 7:
                strengths.append(cs['criterion_name'])
            elif cs['raw_score'] <= 4:
                weaknesses.append(cs['criterion_name'])
        return strengths, weaknesses

    rec_strengths, rec_weaknesses = get_strengths_weaknesses(recommendation)
    runner_strengths, runner_weaknesses = get_strengths_weaknesses(runner_up)

    # --- Trade-off analysis between top 2 ---
    rec_leads = []
    runner_leads = []
    tied = []

    rec_scores_by_criterion = {
        cs['criterion_id']: cs['raw_score']
        for cs in recommendation['criterion_scores']
        if cs['raw_score'] is not None
    }
    runner_scores_by_criterion = {
        cs['criterion_id']: cs['raw_score']
        for cs in runner_up['criterion_scores']
        if cs['raw_score'] is not None
    }

    for criterion in criteria:
        r1 = rec_scores_by_criterion.get(criterion.id)
        r2 = runner_scores_by_criterion.get(criterion.id)
        if r1 is None or r2 is None:
            continue
        diff = r1 - r2
        entry = {
            'criterion': criterion.name,
            'weight': criterion.weight,
            'rec_score': r1,
            'runner_score': r2,
            'diff': round(abs(diff), 1),
        }
        if diff > 0.5:
            rec_leads.append(entry)
        elif diff < -0.5:
            runner_leads.append(entry)
        else:
            tied.append(entry)

    # Sort by weight × diff for most impactful trade-offs
    rec_leads.sort(key=lambda x: x['weight'] * x['diff'], reverse=True)
    runner_leads.sort(key=lambda x: x['weight'] * x['diff'], reverse=True)

    # --- Gap analysis ---
    score_gap = recommendation['normalized_score'] - runner_up['normalized_score']
    if score_gap < 5:
        gap_label = 'very close'
    elif score_gap < 15:
        gap_label = 'moderate'
    else:
        gap_label = 'significant'

    # --- Generate prose summary ---
    summary_parts = []

    # Opening
    summary_parts.append(
        f"{rec_option.name} leads with a score of "
        f"{recommendation['normalized_score']}%, followed by "
        f"{runner_option.name} at {runner_up['normalized_score']}%. "
        f"The gap between them is {gap_label}."
    )

    # Recommendation strengths
    if rec_strengths:
        top_strengths = rec_strengths[:3]
        summary_parts.append(
            f"{rec_option.name} scores particularly well in "
            f"{', '.join(top_strengths)}."
        )

    # Runner-up advantage
    if runner_leads:
        top_runner_leads = [x['criterion'] for x in runner_leads[:2]]
        summary_parts.append(
            f"{runner_option.name} has the advantage in "
            f"{', '.join(top_runner_leads)}, which may matter depending on your priorities."
        )

    # Disqualifier warning
    for result in results:
        if result['has_disqualifier']:
            fails = ', '.join(result['mandatory_fails'])
            summary_parts.append(
                f"⚠ {result['option'].name} falls below the minimum threshold on mandatory "
                f"criteria: {fails}."
            )
            break

    summary_text = ' '.join(summary_parts)

    return {
        'summary': summary_text,
        'recommendation': {
            'option': rec_option,
            'score': recommendation['normalized_score'],
            'strengths': rec_strengths[:4],
            'weaknesses': rec_weaknesses[:3],
        },
        'runner_up': {
            'option': runner_option,
            'score': runner_up['normalized_score'],
            'strengths': runner_strengths[:4],
            'weaknesses': runner_weaknesses[:3],
        },
        'trade_offs': {
            'rec_leads': rec_leads[:4],
            'runner_leads': runner_leads[:4],
            'tied': tied[:3],
            'gap_label': gap_label,
            'score_gap': round(score_gap, 1),
        },
        'all_results': results,
    }

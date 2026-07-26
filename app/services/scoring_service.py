"""
Scoring Service — the calculation heart of Prism.

Weighted Score Formula:
  For each Option O and Criterion C:
    weighted_contribution(O, C) = raw_score(O, C) * weight(C)

  Total Score:
    total(O) = Σ weighted_contribution(O, C) for all C with a score

  Max Possible:
    max_possible = Σ (10 * weight(C)) for all C

  Normalized Score:
    normalized(O) = (total(O) / max_possible) * 100  if max_possible > 0 else 0

Ranking: options sorted by normalized_score descending.
Disqualifier: if any mandatory criterion has raw_score < 5, option is flagged.
"""

from app.models import Score, Criterion, Option
from app.extensions import db


def calculate_results(decision):
    """
    Returns a dict with full comparison results for a decision.
    """
    criteria = decision.criteria.order_by(Criterion.sort_order).all()
    options = decision.options.order_by(Option.sort_order).all()

    if not criteria or not options:
        return None

    total_weight = sum(c.weight for c in criteria)
    max_possible = sum(c.weight * 10 for c in criteria) if criteria else 0

    # Build score lookup: {(criterion_id, option_id): Score}
    all_scores = Score.query.filter_by(decision_id=decision.id).all()
    score_map = {(s.criterion_id, s.option_id): s for s in all_scores}

    results = []
    for option in options:
        total = 0.0
        scored_weight = 0.0
        criterion_scores = []
        has_disqualifier = False
        mandatory_fails = []

        for criterion in criteria:
            score_obj = score_map.get((criterion.id, option.id))
            raw = score_obj.raw_score if score_obj else None

            if raw is not None:
                contribution = raw * criterion.weight
                total += contribution
                scored_weight += criterion.weight

                # Flag mandatory criterion with low score
                if criterion.is_mandatory and raw < 5:
                    has_disqualifier = True
                    mandatory_fails.append(criterion.name)

            criterion_scores.append({
                'criterion_id': criterion.id,
                'criterion_name': criterion.name,
                'weight': criterion.weight,
                'is_mandatory': criterion.is_mandatory,
                'raw_score': raw,
                'score_obj': score_obj,
            })

        # Normalized score based on criteria that were actually scored
        scored_max = scored_weight * 10 if scored_weight > 0 else 1
        normalized = (total / scored_max * 100) if scored_weight > 0 else 0

        # Coverage: how complete is the scoring?
        coverage = (scored_weight / total_weight * 100) if total_weight > 0 else 0

        results.append({
            'option': option,
            'criterion_scores': criterion_scores,
            'total_weighted': round(total, 2),
            'normalized_score': round(normalized, 1),
            'coverage': round(coverage, 1),
            'has_disqualifier': has_disqualifier,
            'mandatory_fails': mandatory_fails,
        })

    # Sort by normalized score descending
    results.sort(key=lambda x: (not x['has_disqualifier'], x['normalized_score']),
                 reverse=True)

    # Assign ranks
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return {
        'criteria': criteria,
        'options': options,
        'results': results,
        'max_possible': max_possible,
        'total_weight': total_weight,
        'score_map': score_map,
        'recommendation': results[0] if results else None,
        'runner_up': results[1] if len(results) > 1 else None,
    }


def get_score_matrix(decision):
    """
    Returns the score matrix as a 2D dict:
    { option_id: { criterion_id: raw_score } }
    """
    all_scores = Score.query.filter_by(decision_id=decision.id).all()
    matrix = {}
    for score in all_scores:
        if score.option_id not in matrix:
            matrix[score.option_id] = {}
        matrix[score.option_id][score.criterion_id] = score.raw_score
    return matrix


def upsert_score(decision_id, criterion_id, option_id, raw_score, notes=None):
    """
    Insert or update a score. Returns the score object.
    """
    score = Score.query.filter_by(
        criterion_id=criterion_id,
        option_id=option_id
    ).first()

    if score is None:
        score = Score(
            decision_id=decision_id,
            criterion_id=criterion_id,
            option_id=option_id,
            raw_score=raw_score,
            notes=notes,
        )
        db.session.add(score)
    else:
        score.raw_score = raw_score
        if notes is not None:
            score.notes = notes

    db.session.commit()
    return score

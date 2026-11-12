"""Score of a match: an integer from 0 to 100 (decision accepted Nov 11, 2026).

The STATUS picks the band, the criteria results place the score INSIDE the band:

    status               band      score
    eligible             70-100    70 + 30 * ratio
    partially_eligible   40-69     40 + 29 * ratio
    not_eligible          0-39      0 + 39 * ratio

ratio = sum(weight * points) / sum(weight), over every evaluated criterion
(scheme and program together); 1 when there is no criterion.
    weight: hard 3, as_a_rule 2, soft 1
    points: pass 1, missing 0.5 (unknown is not a fail), fail 0

The bands make it impossible for a worse status to score higher than a better one.
The score is a ranking aid, not a probability of being selected.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from ai.matching.criterion import CriterionResult, Outcome
from ai.matching.engine import Status

WEIGHTS: dict[str, int] = {"hard": 3, "as_a_rule": 2, "soft": 1}
POINTS: dict[Outcome, float] = {Outcome.PASS: 1.0, Outcome.MISSING: 0.5, Outcome.FAIL: 0.0}

# status -> (lowest score of the band, width of the band)
BANDS: dict[Status, tuple[int, int]] = {
    Status.ELIGIBLE: (70, 30),
    Status.PARTIALLY_ELIGIBLE: (40, 29),
    Status.NOT_ELIGIBLE: (0, 39),
}


def ratio(results: Sequence[CriterionResult]) -> float:
    total = sum(WEIGHTS[r.strength] for r in results)
    if total == 0:
        return 1.0
    return sum(WEIGHTS[r.strength] * POINTS[r.outcome] for r in results) / total


def compute_score(status: Status, results: Sequence[CriterionResult]) -> int:
    low, width = BANDS[status]
    return math.floor(low + width * ratio(results) + 0.5)   # round half up (Python's round() is banker's rounding)

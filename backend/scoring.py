"""Configurable scoring-band resolution for risk methodologies (NR-011).

Kept deliberately small: given a methodology's `scoring_bands` (or none) and
a score, resolve which band it falls in. No matrix-builder UI, no per-cell
configuration — just banded thresholds, which is what every methodology in
this app actually needs (mapping a numeric score to a qualitative label).
"""

from typing import Optional

import models

DEFAULT_BANDS = [
    {"min_score": 20, "max_score": 25, "label": "Critical", "color": "#dc2626"},
    {"min_score": 12, "max_score": 19, "label": "High", "color": "#f97316"},
    {"min_score": 6, "max_score": 11, "label": "Medium", "color": "#facc15"},
    {"min_score": 0, "max_score": 5, "label": "Low", "color": "#22c55e"},
]


def resolve_band(methodology: Optional["models.RiskMethodology"], score: Optional[float]) -> Optional[dict]:
    if score is None:
        return None
    bands = (methodology.scoring_bands if methodology else None) or DEFAULT_BANDS
    for band in bands:
        if band["min_score"] <= score <= band["max_score"]:
            return band
    return None

"""DQ score trend analysis over a dataset's run history (no ML).

Trend score (0–100, 50 = flat):
  momentum  = 50 + 5 × slope            (slope = least-squares pp change per run)
  stability = 100 − 4 × volatility      (volatility = std-dev of scores)
  trend_score = 0.7 × momentum + 0.3 × stability
"""
from __future__ import annotations

import statistics
from typing import Any

SLOPE_FLAT_PP = 0.5
MOMENTUM_PER_PP = 5.0
VOLATILITY_PENALTY = 4.0
MOMENTUM_WEIGHT = 0.7


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _slope(scores: list[float]) -> float:
    n = len(scores)
    xs = range(n)
    x_mean = (n - 1) / 2
    y_mean = sum(scores) / n
    denom = sum((x - x_mean) ** 2 for x in xs)
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, scores)) / denom


def compute_trend(run_history: list[dict]) -> dict[str, Any]:
    scores = [float(r["dq_score"]) for r in run_history if r.get("dq_score") is not None]
    n = len(scores)
    if n == 0:
        return {"runs": 0, "direction": "NoData", "trend_score": None}

    latest = scores[-1]
    base = {
        "runs": n,
        "first_score": scores[0],
        "latest_score": latest,
        "best_score": max(scores),
        "worst_score": min(scores),
        "average_score": round(sum(scores) / n, 2),
    }
    if n == 1:
        return {**base, "direction": "Baseline", "trend_score": None,
                "note": "Run analysis again to compute a trend."}

    slope = _slope(scores)
    volatility = statistics.pstdev(scores)
    momentum = _clamp(50 + MOMENTUM_PER_PP * slope)
    stability = _clamp(100 - VOLATILITY_PENALTY * volatility)
    trend_score = MOMENTUM_WEIGHT * momentum + (1 - MOMENTUM_WEIGHT) * stability

    if slope > SLOPE_FLAT_PP:
        direction = "Improving"
    elif slope < -SLOPE_FLAT_PP:
        direction = "Declining"
    else:
        direction = "Stable"

    intercept = base["average_score"] - slope * (n - 1) / 2
    return {
        **base,
        "direction": direction,
        "trend_score": round(trend_score, 1),
        "slope_per_run": round(slope, 2),
        "volatility": round(volatility, 2),
        "momentum": round(momentum, 1),
        "stability": round(stability, 1),
        "change_total": round(latest - scores[0], 2),
        "change_last": round(latest - scores[-2], 2),
        "forecast_next": round(_clamp(intercept + slope * n), 2),
    }

"""Simple previous-vs-current anomaly detection (no ML)."""
from __future__ import annotations

from typing import Any


DEFAULT_MARGINS = {
    "null_rate_spike_pp": 10.0,  # percentage points
    "volume_drop_pct": 20.0,
    "freshness_delay_days": 3,
    "dimension_drop_pp": 10.0,
}


def detect_anomalies(current: dict, previous: dict | None, margins: dict | None = None) -> list[dict[str, Any]]:
    if not previous:
        return []

    m = {**DEFAULT_MARGINS, **(margins or {})}
    anomalies: list[dict[str, Any]] = []

    curr_null = current.get("null_rate", 0)
    prev_null = previous.get("null_rate", 0)
    null_delta = curr_null - prev_null
    if null_delta > m["null_rate_spike_pp"]:
        anomalies.append(
            {
                "type": "null_rate_spike",
                "message": f"Null-rate spike: {prev_null}% → {curr_null}% (+{round(null_delta, 1)} pp)",
                "previous": prev_null,
                "current": curr_null,
                "change": round(null_delta, 2),
            }
        )

    curr_vol = current.get("record_count", 0)
    prev_vol = previous.get("record_count", 0) or 1
    vol_drop = (prev_vol - curr_vol) / prev_vol * 100
    if vol_drop > m["volume_drop_pct"]:
        anomalies.append(
            {
                "type": "volume_drop",
                "message": f"Record/volume drop: {prev_vol} → {curr_vol} (−{round(vol_drop, 1)}%)",
                "previous": prev_vol,
                "current": curr_vol,
                "change": round(vol_drop, 2),
            }
        )

    curr_fresh = current.get("freshness_delay_days", 0)
    prev_fresh = previous.get("freshness_delay_days", 0)
    fresh_delta = curr_fresh - prev_fresh
    if fresh_delta > m["freshness_delay_days"]:
        anomalies.append(
            {
                "type": "freshness_delay",
                "message": f"Freshness delay increased: {prev_fresh}d → {curr_fresh}d",
                "previous": prev_fresh,
                "current": curr_fresh,
                "change": fresh_delta,
            }
        )

    curr_dims = current.get("dimensions") or {}
    prev_dims = previous.get("dimensions") or {}
    for dim, curr_val in curr_dims.items():
        prev_val = prev_dims.get(dim)
        if prev_val is None:
            continue
        drop = prev_val - curr_val
        if drop > m["dimension_drop_pp"]:
            anomalies.append(
                {
                    "type": "dimension_score_drop",
                    "dimension": dim,
                    "message": f"{dim.title()} score drop: {prev_val}% → {curr_val}% (−{round(drop, 1)} pp)",
                    "previous": prev_val,
                    "current": curr_val,
                    "change": round(drop, 2),
                }
            )

    return anomalies

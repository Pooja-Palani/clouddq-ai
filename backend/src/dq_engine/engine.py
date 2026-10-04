"""DQ engine orchestration: S3 → profile → score → issues → anomalies."""
from __future__ import annotations

from typing import Any

from .anomalies import detect_anomalies
from .dimensions import compute_dimensions
from .profiler import profile_csv
from .rules import evaluate_rules, severity_breakdown


def run_analysis(csv_text: str, previous_run: dict | None = None) -> dict[str, Any]:
    profile = profile_csv(csv_text)
    # Strip rows from persisted profile later; keep for scoring
    score = compute_dimensions(profile)
    issues = evaluate_rules(score, profile)
    severity = severity_breakdown(issues)

    null_cells = score["details"]["completeness"].get("null_cells", 0)
    total_cells = score["details"]["completeness"].get("total_cells", 1) or 1
    null_rate = round(null_cells / total_cells * 100, 2)

    current_signals = {
        "null_rate": null_rate,
        "record_count": profile["record_count"],
        "freshness_delay_days": score["details"]["timeliness"].get("freshness_delay_days", 0),
        "dimensions": score["dimensions"],
        "dq_score": score["dq_score"],
    }

    previous_signals = None
    if previous_run:
        previous_signals = {
            "null_rate": previous_run.get("null_rate", 0),
            "record_count": previous_run.get("record_count", 0),
            "freshness_delay_days": previous_run.get("freshness_delay_days", 0),
            "dimensions": previous_run.get("dimensions") or {},
            "dq_score": previous_run.get("dq_score", 0),
        }

    anomalies = detect_anomalies(current_signals, previous_signals)

    # Persistable profile (no raw rows)
    persist_profile = {
        "record_count": profile["record_count"],
        "column_count": profile["column_count"],
        "columns": profile["columns"],
        "column_profiles": [
            {k: v for k, v in c.items() if k != "sample_values" or True}
            for c in profile["column_profiles"]
        ],
    }
    # trim sample_values for storage size
    for c in persist_profile["column_profiles"]:
        c["sample_values"] = c.get("sample_values", [])[:5]

    return {
        "dq_score": score["dq_score"],
        "health": score["health"],
        "fit_for_analytics": score["fit_for_analytics"],
        "fit_for_use": score["fit_for_use"],
        "dimensions": score["dimensions"],
        "weights": score["weights"],
        "details": score["details"],
        "heatmap": score["heatmap"],
        "issues": issues,
        "severity": severity,
        "anomalies": anomalies,
        "null_rate": null_rate,
        "record_count": profile["record_count"],
        "freshness_delay_days": current_signals["freshness_delay_days"],
        "profile": persist_profile,
        "rule_coverage": {
            "rules_evaluated": 6 + sum(
                1 for c in profile["column_profiles"] if c["null_rate"] > 20
            ),
            "rules_failed": len(issues),
        },
        "pii_hints": _pii_hints(profile),
    }


def _pii_hints(profile: dict) -> list[dict]:
    hints = []
    for col in profile["column_profiles"]:
        lower = col["name"].lower()
        if col["type"] == "email" or "email" in lower:
            hints.append({"column": col["name"], "type": "email"})
        elif col["type"] == "phone" or "phone" in lower:
            hints.append({"column": col["name"], "type": "phone"})
        elif any(k in lower for k in ("ssn", "passport", "aadhaar", "pan")):
            hints.append({"column": col["name"], "type": "identifier"})
    return hints

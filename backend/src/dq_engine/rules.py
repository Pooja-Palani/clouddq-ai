"""Rule evaluation → issues with severity."""
from __future__ import annotations

import uuid
from typing import Any


DEFAULT_RULES = [
    {
        "rule_id": "completeness_overall",
        "name": "Overall Completeness",
        "dimension": "completeness",
        "threshold": 95,
        "severity": "HIGH",
    },
    {
        "rule_id": "validity_overall",
        "name": "Overall Validity",
        "dimension": "validity",
        "threshold": 90,
        "severity": "MEDIUM",
    },
    {
        "rule_id": "uniqueness_overall",
        "name": "Key Uniqueness",
        "dimension": "uniqueness",
        "threshold": 98,
        "severity": "HIGH",
    },
    {
        "rule_id": "consistency_overall",
        "name": "Format Consistency",
        "dimension": "consistency",
        "threshold": 90,
        "severity": "LOW",
    },
    {
        "rule_id": "accuracy_overall",
        "name": "Value Accuracy",
        "dimension": "accuracy",
        "threshold": 95,
        "severity": "MEDIUM",
    },
    {
        "rule_id": "timeliness_overall",
        "name": "Data Timeliness",
        "dimension": "timeliness",
        "threshold": 85,
        "severity": "MEDIUM",
    },
]


def evaluate_rules(score_result: dict, profile: dict) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    dimensions = score_result["dimensions"]

    for rule in DEFAULT_RULES:
        dim = rule["dimension"]
        current = dimensions.get(dim, 100)
        passed = current >= rule["threshold"]
        if not passed:
            issues.append(
                {
                    "issue_id": str(uuid.uuid4()),
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["name"],
                    "dimension": dim,
                    "threshold": rule["threshold"],
                    "current_score": current,
                    "result": "FAIL",
                    "severity": rule["severity"],
                    "status": "OPEN",
                    "message": (
                        f"{rule['name']} failed: score {current}% "
                        f"below threshold {rule['threshold']}%"
                    ),
                }
            )

    # Column-level completeness issues for critical columns
    for col in profile.get("column_profiles", []):
        if col["null_rate"] > 20:
            severity = "HIGH" if col["null_rate"] > 40 else "MEDIUM"
            issues.append(
                {
                    "issue_id": str(uuid.uuid4()),
                    "rule_id": f"col_completeness_{col['name']}",
                    "rule_name": f"{col['name']} Completeness",
                    "dimension": "completeness",
                    "threshold": 80,
                    "current_score": round(100 - col["null_rate"], 2),
                    "result": "FAIL",
                    "severity": severity,
                    "status": "OPEN",
                    "column": col["name"],
                    "message": (
                        f"Column {col['name']} has {col['null_rate']}% missing values"
                    ),
                }
            )

    # Severity breakdown
    return issues


def severity_breakdown(issues: list[dict]) -> dict[str, int]:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for issue in issues:
        sev = issue.get("severity", "INFO")
        counts[sev] = counts.get(sev, 0) + 1
    return {
        "high": counts.get("HIGH", 0) + counts.get("CRITICAL", 0),
        "medium": counts.get("MEDIUM", 0) + counts.get("WARNING", 0),
        "low": counts.get("LOW", 0) + counts.get("INFO", 0),
        "total": len(issues),
    }

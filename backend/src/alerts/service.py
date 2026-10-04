"""Alerts and issue lifecycle (soft correction workflow)."""
from __future__ import annotations

from auth import require_role
from store import dynamo


def create_alert(user: dict, body: dict) -> dict:
    require_role(user, "BusinessUser")
    dataset_id = body.get("datasetId")
    if not dataset_id:
        raise ValueError("datasetId is required")
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")

    score = meta.get("latestScore")
    health = meta.get("latestHealth")
    if health not in {"WARNING", "CRITICAL"} and (score is None or score >= 80):
        # Allow override with force, but default gate for low/critical
        if not body.get("force"):
            raise ValueError("Alerts are intended for Warning/Critical datasets")

    alert_id = dynamo.new_id()
    now = dynamo.now_iso()
    data_user_id = meta.get("ownerId")
    item = {
        "PK": f"ALERT#{alert_id}",
        "SK": "META",
        "entityType": "ALERT",
        "alertId": alert_id,
        "datasetId": dataset_id,
        "datasetName": meta.get("name"),
        "fromUserId": user["sub"],
        "fromEmail": user.get("email"),
        "toUserId": data_user_id,
        "note": body.get("note") or "Quality below acceptable threshold",
        "status": "OPEN",
        "dqScore": score,
        "health": health,
        "createdAt": now,
        "updatedAt": now,
        "history": [
            {
                "status": "OPEN",
                "at": now,
                "note": body.get("note") or "Business alert raised",
                "by": user.get("email") or user["sub"],
            }
        ],
        "GSI1PK": f"USER#{data_user_id}",
        "GSI1SK": f"ALERT#{now}",
    }
    dynamo.put_item(item)

    timeline = list(meta.get("timeline") or [])
    timeline.append({"status": "AlertRaised", "at": now, "note": item["note"]})
    dynamo.update_item(
        f"DATASET#{dataset_id}",
        "META",
        {
            "workflowStatus": "AlertRaised",
            "alertId": alert_id,
            "timeline": timeline,
        },
    )
    return _public_alert(item)


def list_alerts(user: dict) -> list[dict]:
    if user["role"] == "DataUser":
        items = dynamo.query_gsi1(f"USER#{user['sub']}", "ALERT#")
        return [_public_alert(i) for i in items]
    # Business: scan alerts they created (demo-scale)
    items = dynamo.scan_entity("ALERT#")
    mine = [
        i
        for i in items
        if i.get("SK") == "META" and i.get("fromUserId") == user["sub"]
    ]
    return [_public_alert(i) for i in mine]


def get_alert(user: dict, alert_id: str) -> dict:
    item = dynamo.get_item(f"ALERT#{alert_id}", "META")
    if not item:
        raise LookupError("Alert not found")
    if user["role"] == "DataUser" and item.get("toUserId") != user["sub"]:
        raise PermissionError("Not your alert")
    if user["role"] == "BusinessUser" and item.get("fromUserId") != user["sub"]:
        raise PermissionError("Not your alert")
    return _public_alert(item)


def _append_issue_history(issue: dict, status: str, user: dict, note: str) -> list:
    history = list(issue.get("history") or [])
    history.append(
        {
            "status": status,
            "at": dynamo.now_iso(),
            "note": note,
            "by": user.get("email") or user["sub"],
        }
    )
    return history


def assign_issue(user: dict, issue_id: str, body: dict) -> dict:
    require_role(user, "DataUser")
    dataset_id = body.get("datasetId")
    if not dataset_id:
        raise ValueError("datasetId is required")
    issue = dynamo.get_item(f"DATASET#{dataset_id}", f"ISSUE#{issue_id}")
    if not issue:
        raise LookupError("Issue not found")
    assignee = body.get("assignedTo") or user["sub"]
    history = _append_issue_history(issue, "ASSIGNED", user, body.get("note") or "Assigned")
    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        f"ISSUE#{issue_id}",
        {"status": "ASSIGNED", "assignedTo": assignee, "history": history},
    )
    return _public_issue(updated)


def acknowledge_issue(user: dict, issue_id: str, body: dict) -> dict:
    require_role(user, "DataUser")
    dataset_id = body.get("datasetId")
    if not dataset_id:
        raise ValueError("datasetId is required")
    issue = dynamo.get_item(f"DATASET#{dataset_id}", f"ISSUE#{issue_id}")
    if not issue:
        raise LookupError("Issue not found")
    history = _append_issue_history(
        issue, "IN_PROGRESS", user, body.get("note") or "Acknowledged — investigating"
    )
    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        f"ISSUE#{issue_id}",
        {"status": "IN_PROGRESS", "history": history},
    )
    # Move dataset into correction if alert exists
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if meta and meta.get("workflowStatus") == "AlertRaised":
        timeline = list(meta.get("timeline") or [])
        timeline.append(
            {
                "status": "InCorrection",
                "at": dynamo.now_iso(),
                "note": "Data user acknowledged alert",
            }
        )
        dynamo.update_item(
            f"DATASET#{dataset_id}",
            "META",
            {"workflowStatus": "InCorrection", "timeline": timeline},
        )
    return _public_issue(updated)


def resolve_issue(user: dict, issue_id: str, body: dict) -> dict:
    require_role(user, "DataUser")
    dataset_id = body.get("datasetId")
    if not dataset_id:
        raise ValueError("datasetId is required")
    issue = dynamo.get_item(f"DATASET#{dataset_id}", f"ISSUE#{issue_id}")
    if not issue:
        raise LookupError("Issue not found")

    # Re-validation: latest run must pass the related rule/dimension
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    dims = meta.get("latestDimensions") or {}
    dimension = issue.get("dimension")
    threshold = issue.get("threshold", 0)
    current = dims.get(dimension)
    if current is None:
        raise ValueError("No latest analysis to re-validate against — re-run analysis first")
    if current < threshold:
        raise ValueError(
            f"Re-validation failed: {dimension} is {current}% (threshold {threshold}%). "
            "Re-run analysis after fixing data."
        )

    history = _append_issue_history(
        issue,
        "RESOLVED",
        user,
        body.get("note") or f"Re-validation passed ({dimension}={current}%)",
    )
    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        f"ISSUE#{issue_id}",
        {"status": "RESOLVED", "history": history, "resolvedAt": dynamo.now_iso()},
    )

    # Close alert if all HIGH issues resolved
    if meta.get("alertId"):
        issues = dynamo.query_pk(f"DATASET#{dataset_id}", "ISSUE#")
        open_high = [
            i
            for i in issues
            if i.get("severity") in {"HIGH", "CRITICAL"} and i.get("status") != "RESOLVED"
            and i.get("issue_id") != issue_id
        ]
        # account for current issue now resolved
        if not open_high:
            alert = dynamo.get_item(f"ALERT#{meta['alertId']}", "META")
            if alert:
                ah = list(alert.get("history") or [])
                ah.append(
                    {
                        "status": "RESOLVED",
                        "at": dynamo.now_iso(),
                        "note": "Issues resolved after re-validation",
                        "by": user.get("email") or user["sub"],
                    }
                )
                dynamo.update_item(
                    f"ALERT#{meta['alertId']}",
                    "META",
                    {"status": "RESOLVED", "history": ah},
                )
            timeline = list(meta.get("timeline") or [])
            timeline.append(
                {
                    "status": "Resolved",
                    "at": dynamo.now_iso(),
                    "note": "Alert resolved",
                }
            )
            dynamo.update_item(
                f"DATASET#{dataset_id}",
                "META",
                {"workflowStatus": "Resolved", "timeline": timeline},
            )

    return _public_issue(updated)


def reopen_issue(user: dict, issue_id: str, body: dict) -> dict:
    dataset_id = body.get("datasetId")
    if not dataset_id:
        raise ValueError("datasetId is required")
    issue = dynamo.get_item(f"DATASET#{dataset_id}", f"ISSUE#{issue_id}")
    if not issue:
        raise LookupError("Issue not found")
    history = _append_issue_history(
        issue, "OPEN", user, body.get("note") or "Issue reopened"
    )
    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        f"ISSUE#{issue_id}",
        {"status": "OPEN", "history": history},
    )
    return _public_issue(updated)


def _public_alert(item: dict) -> dict:
    omit = {"PK", "SK", "entityType", "GSI1PK", "GSI1SK"}
    return {k: v for k, v in item.items() if k not in omit}


def _public_issue(item: dict) -> dict:
    omit = {"PK", "SK", "entityType"}
    return {k: v for k, v in item.items() if k not in omit}

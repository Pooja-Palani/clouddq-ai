"""Dataset upload, registry, analyze, report, export APIs."""
from __future__ import annotations

import csv
import io
from typing import Any

from auth import require_role
from dq_engine import run_analysis
from store import dynamo, s3


STATUS_FLOW = [
    "Uploaded",
    "Processing",
    "Analyzed",
    "ReportGenerated",
    "Completed",
]


def _append_timeline(meta: dict, status: str, note: str = "") -> list:
    timeline = list(meta.get("timeline") or [])
    timeline.append({"status": status, "at": dynamo.now_iso(), "note": note})
    return timeline


def create_upload_url(user: dict, body: dict) -> dict:
    require_role(user, "DataUser")
    filename = body.get("filename") or "dataset.csv"
    if not filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported")
    dataset_id = dynamo.new_id()
    key = f"datasets/{user['sub']}/{dataset_id}/{filename}"
    url = s3.presigned_put_url(key, content_type=body.get("contentType") or "text/csv")
    return {
        "datasetId": dataset_id,
        "uploadUrl": url,
        "s3Key": key,
        "expiresIn": 900,
    }


def register_dataset(user: dict, body: dict) -> dict:
    require_role(user, "DataUser")
    dataset_id = body.get("datasetId") or dynamo.new_id()
    s3_key = body.get("s3Key")
    name = body.get("name") or body.get("filename") or "Untitled Dataset"
    if not s3_key:
        raise ValueError("s3Key is required")

    now = dynamo.now_iso()
    item = {
        "PK": f"DATASET#{dataset_id}",
        "SK": "META",
        "entityType": "DATASET",
        "datasetId": dataset_id,
        "name": name,
        "filename": body.get("filename") or name,
        "s3Key": s3_key,
        "ownerId": user["sub"],
        "ownerEmail": user.get("email"),
        "status": "Uploaded",
        "workflowStatus": "Completed",
        "timeline": [{"status": "Uploaded", "at": now, "note": "CSV uploaded"}],
        "createdAt": now,
        "updatedAt": now,
        "GSI1PK": f"USER#{user['sub']}",
        "GSI1SK": f"DATASET#{now}",
        "runHistory": [],
        "latestScore": None,
        "latestHealth": None,
        "alertId": None,
        "aiSummary": None,
    }
    dynamo.put_item(item)
    return _public_dataset(item)


def list_datasets(user: dict) -> list[dict]:
    if user["role"] == "DataUser":
        items = dynamo.query_gsi1(f"USER#{user['sub']}", "DATASET#")
        # GSI returns META rows that have GSI1; filter META
        return [_public_dataset(i) for i in items if i.get("SK") == "META" or i.get("entityType") == "DATASET"]
    # Business users see all datasets (demo SaaS)
    items = dynamo.scan_entity("DATASET#")
    return [_public_dataset(i) for i in items if i.get("SK") == "META"]


def get_dataset(user: dict, dataset_id: str) -> dict:
    item = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not item:
        raise LookupError("Dataset not found")
    _assert_can_view(user, item)
    return _public_dataset(item)


def analyze_dataset(user: dict, dataset_id: str, body: dict | None = None) -> dict:
    require_role(user, "DataUser")
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    if meta.get("ownerId") != user["sub"]:
        raise PermissionError("Only the dataset owner can run analysis")

    body = body or {}
    # Optional correction re-upload key
    if body.get("s3Key"):
        meta = dynamo.update_item(
            f"DATASET#{dataset_id}",
            "META",
            {"s3Key": body["s3Key"], "workflowStatus": "Analyzing"},
        )

    timeline = _append_timeline(meta, "Processing", "DQ analysis started")
    dynamo.update_item(
        f"DATASET#{dataset_id}",
        "META",
        {"status": "Processing", "timeline": timeline, "workflowStatus": "Analyzing"},
    )

    csv_text = s3.get_object_text(meta["s3Key"] if not body.get("s3Key") else body["s3Key"])

    # Previous run for anomalies / trends
    runs = dynamo.query_pk(f"DATASET#{dataset_id}", "RUN#")
    runs_sorted = sorted(runs, key=lambda r: r.get("SK", ""), reverse=True)
    previous = runs_sorted[0] if runs_sorted else None

    result = run_analysis(csv_text, previous_run=previous)
    run_ts = dynamo.now_iso()
    run_id = run_ts.replace(":", "-")

    run_item = {
        "PK": f"DATASET#{dataset_id}",
        "SK": f"RUN#{run_ts}",
        "entityType": "RUN",
        "datasetId": dataset_id,
        "runId": run_id,
        "createdAt": run_ts,
        "createdBy": user["sub"],
        **{k: v for k, v in result.items()},
    }
    dynamo.put_item(run_item)

    # Persist issues as separate items
    for issue in result["issues"]:
        issue_item = {
            "PK": f"DATASET#{dataset_id}",
            "SK": f"ISSUE#{issue['issue_id']}",
            "entityType": "ISSUE",
            "datasetId": dataset_id,
            "runId": run_id,
            "assignedTo": user["sub"],
            "history": [
                {
                    "status": "OPEN",
                    "at": run_ts,
                    "note": "Issue generated after rule breach",
                    "by": "system",
                }
            ],
            **issue,
        }
        dynamo.put_item(issue_item)

    run_history = list(meta.get("runHistory") or [])
    run_history.append(
        {
            "runId": run_id,
            "at": run_ts,
            "dq_score": result["dq_score"],
            "health": result["health"],
        }
    )
    # Keep last 20 for trend without new table
    run_history = run_history[-20:]

    timeline = _append_timeline(
        {"timeline": timeline}, "Analyzed", f"DQ score {result['dq_score']}%"
    )
    timeline = _append_timeline(
        {"timeline": timeline}, "ReportGenerated", "Quality report ready"
    )
    timeline = _append_timeline({"timeline": timeline}, "Completed", "Analysis complete")

    workflow = "Completed"
    if meta.get("workflowStatus") in {"AlertRaised", "InCorrection", "Analyzing"}:
        # After correction re-run, mark resolved path if healthy enough
        if result["dq_score"] >= 60:
            workflow = "Resolved"
        else:
            workflow = "Completed"

    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        "META",
        {
            "status": "Completed",
            "workflowStatus": workflow,
            "timeline": timeline,
            "runHistory": run_history,
            "latestScore": result["dq_score"],
            "latestHealth": result["health"],
            "latestFitForUse": result["fit_for_use"],
            "latestSeverity": result["severity"],
            "latestRunId": run_id,
            "latestDimensions": result["dimensions"],
            "aiSummary": None,  # invalidate cached summary
        },
    )
    return {
        "dataset": _public_dataset(updated),
        "run": _public_run(run_item),
    }


def list_runs(user: dict, dataset_id: str) -> list[dict]:
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    _assert_can_view(user, meta)
    runs = dynamo.query_pk(f"DATASET#{dataset_id}", "RUN#")
    runs_sorted = sorted(runs, key=lambda r: r.get("SK", ""))
    return [_public_run(r) for r in runs_sorted]


def get_report(user: dict, dataset_id: str) -> dict:
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    _assert_can_view(user, meta)
    runs = dynamo.query_pk(f"DATASET#{dataset_id}", "RUN#")
    if not runs:
        raise LookupError("No analysis runs yet")
    latest = sorted(runs, key=lambda r: r.get("SK", ""), reverse=True)[0]
    issues = dynamo.query_pk(f"DATASET#{dataset_id}", "ISSUE#")
    # Prefer issues from latest run
    latest_issues = [i for i in issues if i.get("runId") == latest.get("runId")] or issues
    return {
        "dataset": _public_dataset(meta),
        "run": _public_run(latest),
        "issues": [_public_issue(i) for i in latest_issues],
    }


def export_report_csv(user: dict, dataset_id: str) -> dict:
    report = get_report(user, dataset_id)
    run = report["run"]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["DQ Score", run.get("dq_score")])
    writer.writerow(["Health", run.get("health")])
    writer.writerow(["Fit for Analytics", run.get("fit_for_analytics")])
    for dim, val in (run.get("dimensions") or {}).items():
        writer.writerow([f"Dimension:{dim}", val])
    writer.writerow([])
    writer.writerow(["Issue", "Severity", "Status", "Message"])
    for issue in report["issues"]:
        writer.writerow(
            [
                issue.get("rule_name"),
                issue.get("severity"),
                issue.get("status"),
                issue.get("message"),
            ]
        )
    return {
        "filename": f"{report['dataset'].get('name', dataset_id)}_dq_report.csv",
        "contentType": "text/csv",
        "content": buf.getvalue(),
    }


def list_issues(user: dict, dataset_id: str) -> list[dict]:
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    _assert_can_view(user, meta)
    issues = dynamo.query_pk(f"DATASET#{dataset_id}", "ISSUE#")
    return [_public_issue(i) for i in issues]


def enter_correction(user: dict, dataset_id: str, body: dict | None = None) -> dict:
    require_role(user, "DataUser")
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")
    note = (body or {}).get("note") or "Moved to correction flow"
    timeline = _append_timeline(meta, "InCorrection", note)
    updated = dynamo.update_item(
        f"DATASET#{dataset_id}",
        "META",
        {"workflowStatus": "InCorrection", "timeline": timeline},
    )
    return _public_dataset(updated)


def _assert_can_view(user: dict, meta: dict) -> None:
    if user["role"] == "BusinessUser":
        return
    if meta.get("ownerId") == user["sub"]:
        return
    raise PermissionError("Not allowed to view this dataset")


def _public_dataset(item: dict) -> dict:
    keys = [
        "datasetId",
        "name",
        "filename",
        "s3Key",
        "ownerId",
        "ownerEmail",
        "status",
        "workflowStatus",
        "timeline",
        "createdAt",
        "updatedAt",
        "runHistory",
        "latestScore",
        "latestHealth",
        "latestFitForUse",
        "latestSeverity",
        "latestRunId",
        "latestDimensions",
        "alertId",
        "aiSummary",
    ]
    return {k: item.get(k) for k in keys if k in item or True}


def _public_run(item: dict) -> dict:
    omit = {"PK", "SK", "entityType"}
    return {k: v for k, v in item.items() if k not in omit}


def _public_issue(item: dict) -> dict:
    omit = {"PK", "SK", "entityType"}
    return {k: v for k, v in item.items() if k not in omit}

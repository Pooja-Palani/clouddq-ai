"""Amazon Bedrock bridge — metrics JSON only, never raw CSV rows."""
from __future__ import annotations

import json
import os
from typing import Any

import boto3

from store import dynamo

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
# Comma-separated models tried in order after BEDROCK_MODEL_ID.
BEDROCK_FALLBACK_MODEL_IDS = [
    m.strip() for m in os.environ.get("BEDROCK_FALLBACK_MODEL_IDS", "").split(",") if m.strip()
]
BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or None


def _bedrock():
    return boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def _model_ids() -> list[str]:
    return list(dict.fromkeys([BEDROCK_MODEL_ID, *BEDROCK_FALLBACK_MODEL_IDS]))


def build_metrics_payload(run: dict, meta: dict) -> dict[str, Any]:
    """Aggregated metrics only — no raw CSV rows."""
    severity = run.get("severity") or {}
    return {
        "dataset_name": meta.get("name"),
        "dq_score": run.get("dq_score"),
        "health": run.get("health"),
        "fit_for_analytics": run.get("fit_for_analytics"),
        "dimensions": run.get("dimensions"),
        "issues": {
            "high": severity.get("high", 0),
            "medium": severity.get("medium", 0),
            "low": severity.get("low", 0),
            "total": severity.get("total", 0),
        },
        "anomalies": [a.get("message") or a.get("type") for a in (run.get("anomalies") or [])],
        "rule_coverage": run.get("rule_coverage"),
        "record_count": run.get("record_count"),
        "null_rate": run.get("null_rate"),
        "top_issue_messages": [
            i.get("message") for i in (run.get("issues") or [])[:5]
        ],
    }


def generate_summary(user: dict, dataset_id: str) -> dict:
    meta = dynamo.get_item(f"DATASET#{dataset_id}", "META")
    if not meta:
        raise LookupError("Dataset not found")

    # Return cached summary if present and still valid for latest run
    cached = meta.get("aiSummary")
    if cached and cached.get("runId") == meta.get("latestRunId") and not cached.get("offline"):
        return cached

    runs = dynamo.query_pk(f"DATASET#{dataset_id}", "RUN#")
    if not runs:
        raise LookupError("No analysis runs yet")
    latest = sorted(runs, key=lambda r: r.get("SK", ""), reverse=True)[0]
    metrics = build_metrics_payload(latest, meta)

    prompt = (
        "You are a data-quality advisor for business stakeholders. "
        "Given ONLY the aggregated metrics JSON below (no raw data rows), write:\n"
        "1) A short executive summary (3-5 sentences) in plain language.\n"
        "2) Exactly 3 prioritized recommended fixes.\n"
        "Respond in JSON with keys: executive_summary (string), recommendations (array of 3 strings).\n\n"
        f"METRICS_JSON:\n{json.dumps(metrics, indent=2)}"
    )

    summary_text, recommendations, model_used = _invoke_bedrock(prompt, metrics)

    result = {
        "runId": latest.get("runId"),
        "generatedAt": dynamo.now_iso(),
        "executive_summary": summary_text,
        "recommendations": recommendations,
        "metrics_used": metrics,  # transparency: what Bedrock saw
        "model": model_used or "offline-template",
        "offline": model_used is None,
    }
    dynamo.update_item(
        f"DATASET#{dataset_id}",
        "META",
        {"aiSummary": result},
    )
    return result


def _invoke_bedrock(prompt: str, metrics: dict) -> tuple[str, list[str], str | None]:
    """Call Bedrock Converse on each configured model; fall back to a template if all fail."""
    client = _bedrock()
    last_error = "no model configured"
    for model_id in _model_ids():
        try:
            resp = client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 800, "temperature": 0.2},
            )
        except Exception as exc:  # noqa: BLE001 — try the next model, then fall back
            last_error = f"{model_id}: {exc}"
            continue
        text = ""
        for block in resp.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                text += block["text"]
        parsed = _parse_ai_json(text)
        if parsed:
            return parsed["executive_summary"], parsed["recommendations"][:3], model_id
        # If model returned prose, wrap it
        return text.strip(), _fallback_recommendations(metrics), model_id
    summary, recs = _fallback_summary(metrics, last_error)
    return summary, recs, None


def _parse_ai_json(text: str) -> dict | None:
    text = text.strip()
    # Extract the JSON object from fences, preambles or reasoning text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        if "executive_summary" in data and "recommendations" in data:
            return data
    except json.JSONDecodeError:
        return None
    return None


def _fallback_summary(metrics: dict, error: str) -> tuple[str, list[str]]:
    score = metrics.get("dq_score")
    health = metrics.get("health")
    dims = metrics.get("dimensions") or {}
    worst = sorted(dims.items(), key=lambda x: x[1])[:3]
    summary = (
        f"Dataset quality is currently in the {health} range with an overall DQ score of {score}%. "
        f"The weakest dimensions are "
        + ", ".join(f"{k} ({v}%)" for k, v in worst)
        + ". "
        f"There are {metrics.get('issues', {}).get('high', 0)} high-severity and "
        f"{metrics.get('issues', {}).get('medium', 0)} medium-severity issues. "
        "Addressing the top rule failures should improve fitness for analytics. "
        f"(Generated offline — Bedrock unavailable: {error[:120]})"
    )
    return summary, _fallback_recommendations(metrics)


def _fallback_recommendations(metrics: dict) -> list[str]:
    recs = []
    msgs = metrics.get("top_issue_messages") or []
    for m in msgs[:3]:
        recs.append(f"Investigate and remediate: {m}")
    anomalies = metrics.get("anomalies") or []
    for a in anomalies:
        if len(recs) >= 3:
            break
        recs.append(f"Resolve anomaly: {a}")
    while len(recs) < 3:
        defaults = [
            "Investigate missing required identifiers and reduce null rates.",
            "Standardize formats (email, dates, categorical case) for consistency.",
            "Refresh stale records and eliminate future-dated values.",
        ]
        recs.append(defaults[len(recs)])
    return recs[:3]

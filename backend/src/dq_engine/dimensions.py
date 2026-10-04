"""Six-dimension DQ scoring + overall health."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

WEIGHTS = {
    "completeness": 0.25,
    "validity": 0.20,
    "uniqueness": 0.15,
    "consistency": 0.15,
    "accuracy": 0.15,
    "timeliness": 0.10,
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\s\-\+\(\)]{7,20}$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$")
FLOAT_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _empty(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() in {"null", "none", "na", "n/a", "-"}


def _parse_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def score_completeness(profile: dict) -> tuple[float, dict]:
    total = profile["record_count"] * max(profile["column_count"], 1)
    if total == 0:
        return 100.0, {"null_cells": 0, "total_cells": 0}
    null_cells = sum(c["null_count"] for c in profile["column_profiles"])
    score = max(0.0, 100.0 - (null_cells / total * 100))
    return round(score, 2), {"null_cells": null_cells, "total_cells": total}


def score_validity(profile: dict, rows: list[dict]) -> tuple[float, dict]:
    if not rows:
        return 100.0, {"invalid": 0, "checked": 0}
    invalid = 0
    checked = 0
    for col in profile["column_profiles"]:
        name, ctype = col["name"], col["type"]
        for row in rows:
            v = row.get(name, "")
            if _empty(v):
                continue
            checked += 1
            s = str(v).strip()
            ok = True
            if ctype == "email":
                ok = bool(EMAIL_RE.match(s))
            elif ctype == "phone":
                ok = bool(PHONE_RE.match(s))
            elif ctype == "date":
                ok = bool(DATE_RE.match(s))
            elif ctype == "numeric":
                ok = bool(FLOAT_RE.match(s))
            if not ok:
                invalid += 1
    if checked == 0:
        return 100.0, {"invalid": 0, "checked": 0}
    score = max(0.0, 100.0 - (invalid / checked * 100))
    return round(score, 2), {"invalid": invalid, "checked": checked}


def score_uniqueness(profile: dict, rows: list[dict]) -> tuple[float, dict]:
    if not rows:
        return 100.0, {"duplicate_keys": 0}
    # Prefer ID-like columns as keys
    id_cols = [c["name"] for c in profile["column_profiles"] if c["type"] == "id"]
    if not id_cols and profile["columns"]:
        id_cols = [profile["columns"][0]]

    duplicate_keys = 0
    for col in id_cols:
        values = [str(r.get(col, "")).strip().lower() for r in rows if not _empty(r.get(col))]
        counts = Counter(values)
        duplicate_keys += sum(c - 1 for c in counts.values() if c > 1)

    total = len(rows) * max(len(id_cols), 1)
    rate = (duplicate_keys / total * 100) if total else 0
    score = max(0.0, 100.0 - rate)
    return round(score, 2), {"duplicate_keys": duplicate_keys, "id_columns": id_cols}


def score_consistency(profile: dict, rows: list[dict]) -> tuple[float, dict]:
    if not rows:
        return 100.0, {"inconsistent_groups": 0}
    inconsistent = 0
    checked_groups = 0
    for col in profile["column_profiles"]:
        if col["type"] not in {"categorical", "string"}:
            continue
        name = col["name"]
        groups: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            v = row.get(name, "")
            if _empty(v):
                continue
            s = str(v).strip()
            groups[s.lower()].add(s)
        for variants in groups.values():
            checked_groups += 1
            if len(variants) > 1:
                inconsistent += 1
    if checked_groups == 0:
        return 100.0, {"inconsistent_groups": 0}
    score = max(0.0, 100.0 - (inconsistent / checked_groups * 100))
    return round(score, 2), {"inconsistent_groups": inconsistent, "checked_groups": checked_groups}


def score_accuracy(profile: dict, rows: list[dict]) -> tuple[float, dict]:
    if not rows:
        return 100.0, {"out_of_range": 0}
    out = 0
    checked = 0
    for col in profile["column_profiles"]:
        name, ctype = col["name"], col["type"]
        lower = name.lower()
        for row in rows:
            v = row.get(name, "")
            if _empty(v):
                continue
            s = str(v).strip()
            if ctype == "numeric" or "age" in lower:
                if not FLOAT_RE.match(s):
                    continue
                checked += 1
                num = float(s)
                if "age" in lower and (num < 0 or num > 120):
                    out += 1
                elif "amount" in lower or "price" in lower:
                    if num < 0:
                        out += 1
                elif num < -1e12 or num > 1e12:
                    out += 1
            elif ctype == "email":
                checked += 1
                if not EMAIL_RE.match(s):
                    out += 1
    if checked == 0:
        return 100.0, {"out_of_range": 0, "checked": 0}
    score = max(0.0, 100.0 - (out / checked * 100))
    return round(score, 2), {"out_of_range": out, "checked": checked}


def score_timeliness(profile: dict, rows: list[dict]) -> tuple[float, dict]:
    date_cols = [c["name"] for c in profile["column_profiles"] if c["type"] == "date"]
    if not date_cols or not rows:
        return 90.0, {"freshness_delay_days": 0, "future_dates": 0, "note": "no date columns"}

    now = datetime.now(timezone.utc)
    future = 0
    latest: datetime | None = None
    dated = 0
    for col in date_cols:
        for row in rows:
            v = row.get(col, "")
            if _empty(v):
                continue
            dt = _parse_date(str(v))
            if not dt:
                continue
            dated += 1
            if dt > now:
                future += 1
            if latest is None or dt > latest:
                latest = dt

    delay_days = 0
    if latest:
        delay_days = max(0, (now.date() - latest.date()).days)

    # Penalize future dates and staleness (>7 days)
    future_penalty = (future / dated * 50) if dated else 0
    stale_penalty = min(40.0, delay_days * 2) if delay_days > 7 else 0
    score = max(0.0, 100.0 - future_penalty - stale_penalty)
    return round(score, 2), {
        "freshness_delay_days": delay_days,
        "future_dates": future,
        "latest_date": latest.date().isoformat() if latest else None,
    }


def classify_health(score: float) -> dict[str, Any]:
    if score >= 80:
        status = "HEALTHY"
        fit = True
    elif score >= 60:
        status = "WARNING"
        fit = False
    else:
        status = "CRITICAL"
        fit = False
    return {
        "health": status,
        "fit_for_analytics": fit,
        "fit_for_use": fit,
    }


def compute_dimensions(profile: dict) -> dict[str, Any]:
    rows = profile.get("rows") or []
    completeness, c_detail = score_completeness(profile)
    validity, v_detail = score_validity(profile, rows)
    uniqueness, u_detail = score_uniqueness(profile, rows)
    consistency, k_detail = score_consistency(profile, rows)
    accuracy, a_detail = score_accuracy(profile, rows)
    timeliness, t_detail = score_timeliness(profile, rows)

    dimensions = {
        "completeness": completeness,
        "validity": validity,
        "uniqueness": uniqueness,
        "consistency": consistency,
        "accuracy": accuracy,
        "timeliness": timeliness,
    }
    overall = round(
        sum(dimensions[k] * WEIGHTS[k] for k in WEIGHTS),
        2,
    )
    health = classify_health(overall)

    # Column heatmap: blend null rate + validity proxy
    heatmap = []
    for col in profile["column_profiles"]:
        col_score = max(0.0, 100.0 - col["null_rate"])
        if col["type"] in {"email", "phone", "date", "numeric"}:
            # slight penalty already in null; keep simple
            pass
        label = "High Quality"
        if col_score < 60:
            label = "Critical"
        elif col_score < 80:
            label = "Warning"
        elif col_score < 90:
            label = "Good"
        heatmap.append(
            {
                "column": col["name"],
                "score": round(col_score, 2),
                "label": label,
                "null_rate": col["null_rate"],
                "type": col["type"],
            }
        )

    return {
        "dq_score": overall,
        "dimensions": dimensions,
        "weights": WEIGHTS,
        "details": {
            "completeness": c_detail,
            "validity": v_detail,
            "uniqueness": u_detail,
            "consistency": k_detail,
            "accuracy": a_detail,
            "timeliness": t_detail,
        },
        "heatmap": heatmap,
        **health,
    }

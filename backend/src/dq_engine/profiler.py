"""CSV dataset profiling."""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from typing import Any


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\s\-\+\(\)]{7,20}$")
DATE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$"
)
INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    s = str(value).strip()
    return s == "" or s.lower() in {"null", "none", "na", "n/a", "-"}


def infer_column_type(name: str, samples: list[str]) -> str:
    lower = name.lower()
    if "email" in lower:
        return "email"
    if "phone" in lower or "mobile" in lower:
        return "phone"
    if any(k in lower for k in ("date", "created", "updated", "timestamp", "dob")):
        return "date"
    if any(k in lower for k in ("id", "key", "code")):
        return "id"
    if any(k in lower for k in ("age", "amount", "price", "qty", "quantity", "score", "count")):
        return "numeric"
    if any(k in lower for k in ("gender", "sex", "status", "country", "state", "city")):
        return "categorical"

    non_empty = [s for s in samples if not _is_empty(s)]
    if not non_empty:
        return "string"
    email_hits = sum(1 for s in non_empty if EMAIL_RE.match(s))
    if email_hits / len(non_empty) > 0.6:
        return "email"
    date_hits = sum(1 for s in non_empty if DATE_RE.match(s))
    if date_hits / len(non_empty) > 0.6:
        return "date"
    num_hits = sum(1 for s in non_empty if FLOAT_RE.match(s))
    if num_hits / len(non_empty) > 0.8:
        return "numeric"
    return "string"


def profile_csv(text: str) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({k: (v if v is not None else "") for k, v in row.items()})

    record_count = len(rows)
    column_profiles: list[dict[str, Any]] = []

    for col in columns:
        values = [row.get(col, "") for row in rows]
        empty_count = sum(1 for v in values if _is_empty(v))
        non_empty = [v.strip() for v in values if not _is_empty(v)]
        unique_count = len(set(v.lower() for v in non_empty))
        samples = non_empty[:50]
        col_type = infer_column_type(col, samples)
        value_counts = Counter(v.lower() for v in non_empty)
        top_values = [{"value": k, "count": c} for k, c in value_counts.most_common(5)]

        null_rate = (empty_count / record_count * 100) if record_count else 0.0
        column_profiles.append(
            {
                "name": col,
                "type": col_type,
                "null_count": empty_count,
                "null_rate": round(null_rate, 2),
                "unique_count": unique_count,
                "non_empty_count": len(non_empty),
                "top_values": top_values,
                "sample_values": samples[:10],
            }
        )

    return {
        "record_count": record_count,
        "column_count": len(columns),
        "columns": columns,
        "column_profiles": column_profiles,
        "rows": rows,  # kept in-memory for scoring only; never sent to Bedrock
    }

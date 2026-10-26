"""Amazon Comprehend PII detection on a small sample of each column's values."""
from __future__ import annotations

import logging
import os

import boto3

logger = logging.getLogger("clouddq")

PII_MIN_SCORE = float(os.environ.get("PII_MIN_SCORE", "0.8"))
SAMPLE_VALUES = 10
MAX_COLUMNS = 25
# Entity types that are too generic to mark a column as personal data on their own.
IGNORED_TYPES = {"DATE_TIME", "AGE", "URL"}


def _client():
    return boto3.client("comprehend")


def detect_pii_columns(profile: dict, fallback: list[dict]) -> list[dict]:
    """Return one hint per column whose sample values Comprehend classifies as PII.

    Falls back to the name-based hints if Comprehend is unavailable.
    """
    try:
        client = _client()
        hints = []
        for col in profile["column_profiles"][:MAX_COLUMNS]:
            samples = [str(v).strip() for v in (col.get("sample_values") or []) if str(v).strip()]
            if not samples:
                continue
            text = f"{col['name']}: " + "; ".join(samples[:SAMPLE_VALUES])
            entities = client.detect_pii_entities(Text=text[:4000], LanguageCode="en")["Entities"]
            found: dict[str, float] = {}
            for ent in entities:
                if ent["Score"] >= PII_MIN_SCORE and ent["Type"] not in IGNORED_TYPES:
                    found[ent["Type"]] = max(found.get(ent["Type"], 0), ent["Score"])
            if found:
                top = max(found, key=found.get)
                hints.append({
                    "column": col["name"],
                    "type": f"{top} · Amazon Comprehend {round(found[top] * 100)}%",
                    "entities": sorted(found),
                    "source": "comprehend",
                })
        return hints
    except Exception as exc:  # noqa: BLE001 — keep analysis working without Comprehend
        logger.warning("comprehend unavailable: %s", exc)
        return fallback

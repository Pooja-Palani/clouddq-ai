"""Unit tests for DQ engine (no AWS required)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dq_engine.engine import run_analysis  # noqa: E402
from dq_engine.dimensions import classify_health  # noqa: E402


SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_dirty_customers_has_issues():
    text = (SAMPLES / "customers_dirty.csv").read_text()
    result = run_analysis(text)
    assert 0 <= result["dq_score"] <= 100
    assert result["health"] in {"HEALTHY", "WARNING", "CRITICAL"}
    assert "completeness" in result["dimensions"]
    assert len(result["issues"]) >= 1
    assert len(result["heatmap"]) >= 1


def test_clean_employees_high_score():
    text = (SAMPLES / "employees_clean.csv").read_text()
    result = run_analysis(text)
    assert result["dq_score"] >= 80
    assert result["fit_for_use"] is True


def test_anomaly_on_volume_drop():
    text = (SAMPLES / "customers_dirty.csv").read_text()
    first = run_analysis(text)
    previous = {**first, "record_count": first["record_count"] * 3, "null_rate": 0}
    second = run_analysis(text, previous_run=previous)
    types = {a["type"] for a in second["anomalies"]}
    assert "volume_drop" in types


def test_health_bands():
    assert classify_health(87)["health"] == "HEALTHY"
    assert classify_health(70)["health"] == "WARNING"
    assert classify_health(40)["health"] == "CRITICAL"


if __name__ == "__main__":
    test_dirty_customers_has_issues()
    test_clean_employees_high_score()
    test_anomaly_on_volume_drop()
    test_health_bands()
    print("All DQ engine tests passed")

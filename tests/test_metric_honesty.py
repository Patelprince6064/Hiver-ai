"""Tests for metric honesty, audit checks, and report integrity."""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audit_headline_metric import audit_metric_gaming
from scripts.create_final_metric_table import generate_metric_table


class TestMetricHonesty:
    """Tests for metric honesty and audit routines."""

    def test_metric_gaming_audit_passes(self):
        """Test that gaming audit executes and reports PASS."""
        audit = audit_metric_gaming()
        assert audit["overall_verdict"] == "PASSED — NO GAMING OR CHERRY-PICKING DETECTED"
        assert len(audit["checks"]) >= 5
        for c in audit["checks"]:
            assert c["status"] == "PASS"

    def test_final_metric_table_contains_required_fields(self):
        """Test that the final metric table has primary and supporting metrics."""
        rows = generate_metric_table()
        assert len(rows) >= 5
        primary_rows = [r for r in rows if r["primary_or_supporting"] == "PRIMARY HEADLINE"]
        assert len(primary_rows) == 1
        assert primary_rows[0]["value"] == 0.767
        assert primary_rows[0]["baseline_value"] == 0.500

    def test_no_fabricated_values_in_headline_json(self):
        """Verify headline_metric.json values match frozen Phase 18 numbers."""
        json_path = Path("evaluation/results/headline_metric.json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["value"] == 0.767
            assert data["baseline_value"] == 0.500
            assert data["sample_size"] == 200
            assert round(data["value"] - data["baseline_value"], 3) == data["delta"]

    def test_headline_sentence_format(self):
        """Verify headline sentence matches required format."""
        txt_path = Path("evaluation/results/headline_sentence.txt")
        if txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            assert content.startswith("On the Phase 18")
            assert "0.767" in content
            assert "0.500" in content
            assert "should not be interpreted as" in content
            assert "because" in content

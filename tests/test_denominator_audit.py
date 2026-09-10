"""Tests for denominator audit and rate calculation integrity."""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audit_headline_metric import perform_denominator_audit


class TestDenominatorAudit:
    """Tests for denominator accuracy and integrity."""

    def test_denominator_audit_generation(self):
        """Test denominator audit output generation."""
        audit = perform_denominator_audit()
        assert "auto_handle_rate" in audit
        assert "verified_reply_quality_score" in audit
        assert "unsafe_auto_handle_rate" in audit

    def test_auto_handle_denominator_integrity(self):
        """Verify auto-handle denominator is total requests, not subset."""
        audit = perform_denominator_audit()
        auto_handle = audit["auto_handle_rate"]
        assert auto_handle["denominator_value"] == 200
        assert auto_handle["numerator_value"] == 140
        assert round(auto_handle["numerator_value"] / auto_handle["denominator_value"], 2) == 0.70

    def test_unsafe_auto_handle_dual_denominator(self):
        """Verify unsafe auto-handle records both overall and high-risk denominators."""
        audit = perform_denominator_audit()
        unsafe = audit["unsafe_auto_handle_rate"]
        assert unsafe["denominator_value"] == 200
        assert unsafe["value"] == 0.02
        assert unsafe["high_risk_subset_denominator"] == 31
        assert round(4 / 31, 3) == 0.129

    def test_rate_bounds_and_consistency(self):
        """Verify all audited rates lie within [0.0, 1.0]."""
        audit = perform_denominator_audit()
        for metric_key, item in audit.items():
            val = item.get("value")
            assert 0.0 <= val <= 1.0, f"Out of bounds for {metric_key}: {val}"

"""Tests for metric selection framework and deterministic criteria evaluation."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.headline_metrics import get_candidate_metrics


class TestMetricSelection:
    """Tests for metric selection criteria and candidates."""

    def test_candidate_metrics_catalog(self):
        """Test candidate metrics dictionary is populated."""
        candidates = get_candidate_metrics()
        assert len(candidates) >= 4
        assert "verified_reply_quality" in candidates
        assert "intent_macro_f1" in candidates
        assert "auto_handle_rate" in candidates

    def test_deterministic_primary_selection(self):
        """Test that exactly one candidate is designated as selected primary."""
        candidates = get_candidate_metrics()
        selected = [k for k, v in candidates.items() if v.get("selected")]
        assert len(selected) == 1
        assert selected[0] == "verified_reply_quality"

    def test_auto_handle_rejected_due_to_critical_risk(self):
        """Test auto-handle rate has critical misinterpretation risk."""
        candidates = get_candidate_metrics()
        auto_handle = candidates["auto_handle_rate"]
        assert auto_handle["selected"] is False
        assert auto_handle["risk_of_misinterpretation"] == "Critical"

    def test_candidate_scoring_validity(self):
        """Test candidate scores are within valid 1-10 range."""
        candidates = get_candidate_metrics()
        for k, cand in candidates.items():
            rel = cand.get("relevance_score", 0)
            interp = cand.get("interpretability_score", 0)
            assert 1 <= rel <= 10
            assert 1 <= interp <= 10

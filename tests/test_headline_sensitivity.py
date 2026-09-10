"""Tests for headline sensitivity and stability analysis."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.analyze_headline_sensitivity import analyze_sensitivity
from scripts.analyze_headline_stability import analyze_stability


class TestHeadlineSensitivityAndStability:
    """Tests for sensitivity and stability routines."""

    def test_sensitivity_analysis_execution(self):
        """Test sensitivity analysis produces scenarios."""
        res = analyze_sensitivity()
        assert res["baseline_value"] == 0.767
        assert "scenarios" in res
        assert "exclude_hard_10pct" in res["scenarios"]
        assert "strict_annotator_bias" in res["scenarios"]

    def test_sensitivity_scenario_deltas(self):
        """Test that hard cases removal inflates metric and strict annotator deflates."""
        res = analyze_sensitivity()
        hard_dropped = res["scenarios"]["exclude_hard_10pct"]
        strict_annotator = res["scenarios"]["strict_annotator_bias"]

        assert hard_dropped["delta"] > 0.0  # Removing hard cases inflates score
        assert strict_annotator["delta"] < 0.0  # Strict annotator reduces score

    def test_stability_analysis_execution(self):
        """Test stability analysis produces subgroup distributions."""
        res = analyze_stability()
        assert res["overall"]["mean"] == 0.767
        assert "by_difficulty" in res
        assert "common_vs_rare_intents" in res
        assert "stability_verdict" in res

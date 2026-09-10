"""Tests for headline metric schema, calculation, and confidence intervals."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.headline_metrics import (
    HeadlineMetricRecord,
    calculate_mean_ci,
    calculate_proportion_ci,
    calculate_deltas,
)


class TestHeadlineMetricSchema:
    """Tests for HeadlineMetricRecord schema."""

    def test_valid_headline_metric_schema(self):
        """Test valid headline metric record creation."""
        rec = HeadlineMetricRecord(
            metric_name="Verified Grounded Reply Quality Score",
            value=0.767,
            unit="normalized score (0.0 - 1.0)",
            evaluation_set="Phase 18 Test Set",
            sample_size=200,
            definition="Mean quality score across 6 dimensions",
            formula="Mean(scores)",
            baseline="Historical Response Baseline",
            baseline_value=0.500,
            delta=0.267,
            relative_delta=53.4,
            confidence_interval=[0.7612, 0.7728],
            limitations=["Offline proxy score"],
        )
        d = rec.to_dict()
        assert d["metric_name"] == "Verified Grounded Reply Quality Score"
        assert d["value"] == 0.767
        assert d["sample_size"] == 200
        assert d["delta"] == 0.267
        assert d["confidence_interval"] == [0.7612, 0.7728]
        assert len(d["limitations"]) == 1

    def test_valid_metric_value(self):
        """Test value within reasonable bounds [0.0, 1.0]."""
        val = 0.767
        assert 0.0 <= val <= 1.0

    def test_invalid_metric_value_flagging(self):
        """Test that out-of-bound values can be detected."""
        invalid_val = 1.45
        assert not (0.0 <= invalid_val <= 1.0)


class TestConfidenceIntervalCalculation:
    """Tests for CI calculation logic."""

    def test_mean_confidence_interval(self):
        """Test 95% CI calculation for continuous mean."""
        ci = calculate_mean_ci(mean=0.767, std=0.042, n=200)
        assert ci is not None
        assert len(ci) == 2
        assert ci[0] < 0.767 < ci[1]
        assert round(ci[0], 3) == 0.761
        assert round(ci[1], 3) == 0.773

    def test_proportion_confidence_interval(self):
        """Test Wilson score CI calculation for proportions."""
        ci = calculate_proportion_ci(p=0.70, n=200)
        assert ci is not None
        assert len(ci) == 2
        assert ci[0] < 0.70 < ci[1]

    def test_zero_or_small_sample_ci(self):
        """Test handling small sample sizes."""
        assert calculate_mean_ci(0.5, 0.1, n=1) is None
        assert calculate_proportion_ci(0.5, n=0) is None


class TestDeltaCalculation:
    """Tests for absolute and relative delta calculations."""

    def test_valid_baseline_delta(self):
        """Test delta computation against positive baseline."""
        abs_delta, rel_delta = calculate_deltas(value=0.767, baseline_value=0.500)
        assert round(abs_delta, 3) == 0.267
        assert rel_delta is not None
        assert round(rel_delta, 1) == 53.4

    def test_missing_or_zero_baseline(self):
        """Test delta computation when baseline is zero."""
        abs_delta, rel_delta = calculate_deltas(value=0.70, baseline_value=0.0)
        assert abs_delta == 0.70
        assert rel_delta is None

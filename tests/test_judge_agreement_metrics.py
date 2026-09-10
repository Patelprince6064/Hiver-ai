"""Tests for judge agreement metrics."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge_agreement_metrics import (
    calculate_mae,
    calculate_exact_agreement,
    calculate_within_1_agreement,
    calculate_spearman_correlation,
    calculate_pearson_correlation,
    calculate_weighted_kappa,
    calculate_agreement_metrics,
)


class TestMAE:
    """Tests for Mean Absolute Error."""

    def test_perfect_agreement(self):
        """Test MAE with perfect agreement."""
        human = [4.0, 4.0, 4.0]
        llm = [4.0, 4.0, 4.0]
        assert calculate_mae(human, llm) == 0.0

    def test_known_mae(self):
        """Test MAE with known values."""
        human = [4.0, 3.0, 5.0]
        llm = [4.0, 4.0, 4.0]
        expected = (0.0 + 1.0 + 1.0) / 3
        assert abs(calculate_mae(human, llm) - expected) < 0.001

    def test_empty_lists(self):
        """Test MAE with empty lists."""
        assert calculate_mae([], []) == 0.0


class TestExactAgreement:
    """Tests for exact agreement."""

    def test_perfect_agreement(self):
        """Test with perfect agreement."""
        human = [4.0, 4.0, 4.0]
        llm = [4.0, 4.0, 4.0]
        assert calculate_exact_agreement(human, llm) == 1.0

    def test_no_agreement(self):
        """Test with no agreement."""
        human = [1.0, 1.0, 1.0]
        llm = [5.0, 5.0, 5.0]
        assert calculate_exact_agreement(human, llm) == 0.0

    def test_partial_agreement(self):
        """Test with partial agreement."""
        human = [4.0, 3.0, 5.0]
        llm = [4.0, 4.0, 5.0]
        assert abs(calculate_exact_agreement(human, llm) - 2/3) < 0.001


class TestWithin1Agreement:
    """Tests for within-1 agreement."""

    def test_all_within_1(self):
        """Test when all are within 1 point."""
        human = [4.0, 3.0, 5.0]
        llm = [4.0, 4.0, 4.0]
        assert calculate_within_1_agreement(human, llm) == 1.0

    def test_some_outside(self):
        """Test when some are outside 1 point."""
        human = [1.0, 3.0, 5.0]
        llm = [5.0, 3.0, 5.0]
        assert abs(calculate_within_1_agreement(human, llm) - 2/3) < 0.001


class TestSpearmanCorrelation:
    """Tests for Spearman correlation."""

    def test_perfect_correlation(self):
        """Test with perfect correlation."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        corr, p = calculate_spearman_correlation(x, y)
        assert abs(corr - 1.0) < 0.01

    def test_inverse_correlation(self):
        """Test with inverse correlation."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        corr, p = calculate_spearman_correlation(x, y)
        assert abs(corr + 1.0) < 0.01

    def test_too_few_points(self):
        """Test with too few points."""
        x = [1.0, 2.0]
        y = [1.0, 2.0]
        corr, p = calculate_spearman_correlation(x, y)
        assert corr == 0.0


class TestWeightedKappa:
    """Tests for weighted Cohen's kappa."""

    def test_perfect_agreement(self):
        """Test with perfect agreement."""
        human = [1, 2, 3, 4, 5]
        llm = [1, 2, 3, 4, 5]
        kappa = calculate_weighted_kappa(human, llm)
        assert kappa == 1.0

    def test_no_agreement(self):
        """Test with no agreement."""
        human = [1, 1, 1, 1, 1]
        llm = [5, 5, 5, 5, 5]
        kappa = calculate_weighted_kappa(human, llm)
        # Kappa should be low (close to 0 or negative) for no agreement
        assert kappa < 0.5

    def test_empty_lists(self):
        """Test with empty lists."""
        assert calculate_weighted_kappa([], []) == 0.0


class TestAgreementMetrics:
    """Tests for comprehensive agreement metrics."""

    def test_perfect_agreement(self):
        """Test with perfect agreement."""
        human = [4.0, 4.0, 4.0]
        llm = [4.0, 4.0, 4.0]
        metrics = calculate_agreement_metrics(human, llm)
        assert metrics["mae"] == 0.0
        assert metrics["exact_agreement"] == 1.0
        assert metrics["within_1_agreement"] == 1.0

    def test_known_metrics(self):
        """Test with known values."""
        human = [4.0, 3.0, 5.0]
        llm = [4.0, 4.0, 4.0]
        metrics = calculate_agreement_metrics(human, llm)
        assert metrics["n"] == 3
        assert abs(metrics["mae"] - 2/3) < 0.001
        assert abs(metrics["exact_agreement"] - 1/3) < 0.001

    def test_empty_lists(self):
        """Test with empty lists."""
        metrics = calculate_agreement_metrics([], [])
        assert metrics["n"] == 0
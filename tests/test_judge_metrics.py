"""Tests for judge metrics calculations."""

import math
import pytest


def calculate_correlation(x: list[float], y: list[float]) -> tuple[float, float]:
    """Calculate Pearson and Spearman correlation (test helper)."""
    n = len(x)
    if n < 3:
        return 0.0, 0.0

    # Pearson correlation
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
    
    if std_x == 0 or std_y == 0:
        pearson = 0.0
    else:
        pearson = cov_xy / (std_x * std_y)

    # Spearman correlation (rank-based)
    def rank_data(data):
        sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0.0] * len(data)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank
        return ranks

    rank_x = rank_data(x)
    rank_y = rank_data(y)
    
    # Calculate Spearman using Pearson on ranks
    mean_rx = sum(rank_x) / n
    mean_ry = sum(rank_y) / n
    
    cov_rx_ry = sum((rx - mean_rx) * (ry - mean_ry) for rx, ry in zip(rank_x, rank_y)) / n
    std_rx = math.sqrt(sum((rx - mean_rx) ** 2 for rx in rank_x) / n)
    std_ry = math.sqrt(sum((ry - mean_ry) ** 2 for ry in rank_y) / n)
    
    if std_rx == 0 or std_ry == 0:
        spearman = 0.0
    else:
        spearman = cov_rx_ry / (std_rx * std_ry)

    return pearson, spearman


def calculate_agreement_metrics(human_scores: list[float], llm_scores: list[float]) -> dict:
    """Calculate agreement metrics (test helper)."""
    n = len(human_scores)
    if n == 0:
        return {}

    human_mean = sum(human_scores) / n
    llm_mean = sum(llm_scores) / n
    mad = sum(abs(h - l) for h, l in zip(human_scores, llm_scores)) / n
    exact_agreement = sum(1 for h, l in zip(human_scores, llm_scores) if h == l) / n
    within_1 = sum(1 for h, l in zip(human_scores, llm_scores) if abs(h - l) <= 1) / n

    pearson, spearman = calculate_correlation(human_scores, llm_scores)

    return {
        "n_examples": n,
        "human_mean": round(human_mean, 3),
        "llm_mean": round(llm_mean, 3),
        "mean_absolute_difference": round(mad, 3),
        "exact_agreement": round(exact_agreement, 3),
        "within_1_agreement": round(within_1, 3),
        "pearson": round(pearson, 3),
        "spearman": round(spearman, 3),
    }


class TestCorrelation:
    """Tests for correlation calculations."""

    def test_perfect_correlation(self):
        """Test perfect positive correlation."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        pearson, spearman = calculate_correlation(x, y)
        assert pearson == pytest.approx(1.0, abs=0.01)
        assert spearman == pytest.approx(1.0, abs=0.01)

    def test_inverse_correlation(self):
        """Test perfect negative correlation."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        pearson, spearman = calculate_correlation(x, y)
        assert pearson == pytest.approx(-1.0, abs=0.01)
        assert spearman == pytest.approx(-1.0, abs=0.01)

    def test_no_correlation(self):
        """Test no correlation."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0, 1.0, 4.0, 1.0, 5.0]
        pearson, spearman = calculate_correlation(x, y)
        # Should be close to 0
        assert abs(pearson) < 0.5
        assert abs(spearman) < 0.5

    def test_too_few_points(self):
        """Test with too few data points."""
        x = [1.0, 2.0]
        y = [1.0, 2.0]
        pearson, spearman = calculate_correlation(x, y)
        assert pearson == 0.0
        assert spearman == 0.0


class TestAgreementMetrics:
    """Tests for agreement metrics."""

    def test_perfect_agreement(self):
        """Test perfect agreement."""
        human = [4.0, 4.0, 4.0, 4.0]
        llm = [4.0, 4.0, 4.0, 4.0]
        metrics = calculate_agreement_metrics(human, llm)
        assert metrics["exact_agreement"] == 1.0
        assert metrics["within_1_agreement"] == 1.0
        assert metrics["mean_absolute_difference"] == 0.0

    def test_partial_agreement(self):
        """Test partial agreement."""
        human = [4.0, 3.0, 5.0, 4.0]
        llm = [4.0, 4.0, 5.0, 3.0]
        metrics = calculate_agreement_metrics(human, llm)
        assert metrics["exact_agreement"] == 0.5  # 2 out of 4
        assert metrics["within_1_agreement"] == 1.0  # All within 1

    def test_no_agreement(self):
        """Test no agreement."""
        human = [1.0, 1.0, 1.0, 1.0]
        llm = [5.0, 5.0, 5.0, 5.0]
        metrics = calculate_agreement_metrics(human, llm)
        assert metrics["exact_agreement"] == 0.0
        assert metrics["within_1_agreement"] == 0.0

    def test_empty_data(self):
        """Test with empty data."""
        metrics = calculate_agreement_metrics([], [])
        assert metrics == {}
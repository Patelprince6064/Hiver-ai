"""Tests for judge ranking comparison."""

import pytest
import math


def calculate_ranking_correlation(
    human_ranking: list[str],
    llm_ranking: list[str],
) -> dict:
    """Calculate ranking correlation between human and LLM.

    Args:
        human_ranking: List of system names ranked by human (best first).
        llm_ranking: List of system names ranked by LLM (best first).

    Returns:
        Ranking correlation metrics.
    """
    # Convert rankings to scores (higher rank = higher score)
    n = len(human_ranking)
    if n == 0:
        return {"spearman": 0.0, "kendall_tau": 0.0, "agreement": False}

    human_scores = {system: n - i for i, system in enumerate(human_ranking)}
    llm_scores = {system: n - i for i, system in enumerate(llm_ranking)}

    # Check if both rankings have the same systems
    human_set = set(human_ranking)
    llm_set = set(llm_ranking)
    if human_set != llm_set:
        return {"spearman": 0.0, "kendall_tau": 0.0, "agreement": False, "error": "Rankings have different systems"}

    # Calculate Spearman correlation
    x = [human_scores[s] for s in human_ranking]
    y = [llm_scores[s] for s in human_ranking]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)

    if std_x == 0 or std_y == 0:
        spearman = 0.0
    else:
        spearman = cov_xy / (std_x * std_y)

    # Calculate Kendall's tau
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            human_diff = human_scores[human_ranking[i]] - human_scores[human_ranking[j]]
            llm_diff = llm_scores[human_ranking[i]] - llm_scores[human_ranking[j]]

            if human_diff * llm_diff > 0:
                concordant += 1
            elif human_diff * llm_diff < 0:
                discordant += 1

    total_pairs = n * (n - 1) / 2
    kendall_tau = (concordant - discordant) / total_pairs if total_pairs > 0 else 0.0

    # Check if best system is the same
    agreement = human_ranking[0] == llm_ranking[0]

    return {
        "spearman": round(spearman, 4),
        "kendall_tau": round(kendall_tau, 4),
        "agreement": agreement,
        "human_best": human_ranking[0],
        "llm_best": llm_ranking[0],
    }


class TestRankingCorrelation:
    """Tests for ranking correlation."""

    def test_identical_rankings(self):
        """Test with identical rankings."""
        human = ["A", "B", "C", "D"]
        llm = ["A", "B", "C", "D"]
        result = calculate_ranking_correlation(human, llm)
        assert result["spearman"] == 1.0
        assert result["kendall_tau"] == 1.0
        assert result["agreement"] is True

    def test_reversed_rankings(self):
        """Test with reversed rankings."""
        human = ["A", "B", "C", "D"]
        llm = ["D", "C", "B", "A"]
        result = calculate_ranking_correlation(human, llm)
        assert result["spearman"] == -1.0
        assert result["kendall_tau"] == -1.0
        assert result["agreement"] is False

    def test_same_best_different_order(self):
        """Test with same best but different order."""
        human = ["A", "B", "C", "D"]
        llm = ["A", "C", "B", "D"]
        result = calculate_ranking_correlation(human, llm)
        assert result["agreement"] is True
        assert result["spearman"] > 0

    def test_different_best(self):
        """Test with different best system."""
        human = ["A", "B", "C", "D"]
        llm = ["B", "A", "C", "D"]
        result = calculate_ranking_correlation(human, llm)
        assert result["agreement"] is False

    def test_empty_rankings(self):
        """Test with empty rankings."""
        result = calculate_ranking_correlation([], [])
        assert result["spearman"] == 0.0
        assert result["agreement"] is False
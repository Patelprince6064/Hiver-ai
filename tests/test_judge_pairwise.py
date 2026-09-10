"""Tests for judge pairwise comparison."""

import pytest


def calculate_pairwise_agreement(
    human_scores_a: list[float],
    human_scores_b: list[float],
    llm_scores_a: list[float],
    llm_scores_b: list[float],
) -> dict:
    """Calculate pairwise agreement between two systems.

    Args:
        human_scores_a: Human scores for system A.
        human_scores_b: Human scores for system B.
        llm_scores_a: LLM scores for system A.
        llm_scores_b: LLM scores for system B.

    Returns:
        Pairwise agreement metrics.
    """
    n = len(human_scores_a)
    if n == 0:
        return {"agreement_rate": 0.0, "n": 0}

    agreements = 0
    for i in range(n):
        human_better_a = human_scores_a[i] > human_scores_b[i]
        human_better_b = human_scores_b[i] > human_scores_a[i]
        human_tie = human_scores_a[i] == human_scores_b[i]

        llm_better_a = llm_scores_a[i] > llm_scores_b[i]
        llm_better_b = llm_scores_b[i] > llm_scores_a[i]
        llm_tie = llm_scores_a[i] == llm_scores_b[i]

        # Check agreement
        if human_better_a and llm_better_a:
            agreements += 1
        elif human_better_b and llm_better_b:
            agreements += 1
        elif human_tie and llm_tie:
            agreements += 1

    return {
        "agreement_rate": agreements / n,
        "n": n,
        "agreements": agreements,
    }


class TestPairwiseAgreement:
    """Tests for pairwise agreement."""

    def test_perfect_agreement(self):
        """Test with perfect agreement."""
        human_a = [4.0, 3.0, 5.0]
        human_b = [3.0, 4.0, 4.0]
        llm_a = [4.0, 3.0, 5.0]
        llm_b = [3.0, 4.0, 4.0]
        result = calculate_pairwise_agreement(human_a, human_b, llm_a, llm_b)
        assert result["agreement_rate"] == 1.0

    def test_no_agreement(self):
        """Test with no agreement."""
        human_a = [4.0, 4.0, 4.0]
        human_b = [3.0, 3.0, 3.0]
        llm_a = [3.0, 3.0, 3.0]
        llm_b = [4.0, 4.0, 4.0]
        result = calculate_pairwise_agreement(human_a, human_b, llm_a, llm_b)
        assert result["agreement_rate"] == 0.0

    def test_partial_agreement(self):
        """Test with partial agreement."""
        human_a = [4.0, 3.0, 5.0]
        human_b = [3.0, 4.0, 4.0]
        llm_a = [4.0, 4.0, 5.0]
        llm_b = [3.0, 3.0, 4.0]
        result = calculate_pairwise_agreement(human_a, human_b, llm_a, llm_b)
        # Agreement: (4>3, 4>3), (3<4, 4>3 no), (5>4, 5>4)
        assert result["agreement_rate"] == 2/3

    def test_empty_lists(self):
        """Test with empty lists."""
        result = calculate_pairwise_agreement([], [], [], [])
        assert result["agreement_rate"] == 0.0
        assert result["n"] == 0
"""Tests for judge bias analysis."""

import pytest
import math


def calculate_length_bias_analysis(
    replies: list[str],
    human_scores: list[float],
    llm_scores: list[float],
) -> dict:
    """Analyze bias based on reply length.

    Args:
        replies: List of candidate replies.
        human_scores: List of human overall scores.
        llm_scores: List of LLM overall scores.

    Returns:
        Length bias analysis.
    """
    if not replies or len(replies) != len(human_scores) or len(replies) != len(llm_scores):
        return {"error": "Invalid input"}

    # Calculate reply lengths
    lengths = [len(reply.split()) for reply in replies]

    # Calculate correlations
    n = len(lengths)
    if n < 3:
        return {"error": "Too few samples"}

    # Correlation between length and human scores
    mean_len = sum(lengths) / n
    mean_human = sum(human_scores) / n
    mean_llm = sum(llm_scores) / n

    cov_len_human = sum((l - mean_len) * (h - mean_human) for l, h in zip(lengths, human_scores)) / n
    std_len = math.sqrt(sum((l - mean_len) ** 2 for l in lengths) / n)
    std_human = math.sqrt(sum((h - mean_human) ** 2 for h in human_scores) / n)

    if std_len == 0 or std_human == 0:
        corr_len_human = 0.0
    else:
        corr_len_human = cov_len_human / (std_len * std_human)

    # Correlation between length and LLM scores
    cov_len_llm = sum((l - mean_len) * (s - mean_llm) for l, s in zip(lengths, llm_scores)) / n
    std_llm = math.sqrt(sum((s - mean_llm) ** 2 for s in llm_scores) / n)

    if std_len == 0 or std_llm == 0:
        corr_len_llm = 0.0
    else:
        corr_len_llm = cov_len_llm / (std_len * std_llm)

    # Detect bias
    verbosity_bias = False
    if corr_len_llm > 0.3 and corr_len_llm > corr_len_human + 0.2:
        verbosity_bias = True

    return {
        "n_samples": n,
        "mean_length": round(mean_len, 2),
        "corr_length_human": round(corr_len_human, 4),
        "corr_length_llm": round(corr_len_llm, 4),
        "verbosity_bias": verbosity_bias,
        "bias_magnitude": round(corr_len_llm - corr_len_human, 4),
    }


class TestLengthBias:
    """Tests for length bias analysis."""

    def test_no_bias(self):
        """Test with no length bias."""
        replies = ["Short", "Medium length reply", "Longer reply here"]
        human = [3.0, 3.0, 3.0]
        llm = [3.0, 3.0, 3.0]
        result = calculate_length_bias_analysis(replies, human, llm)
        assert "error" not in result
        assert result["verbosity_bias"] is False

    def test_positive_bias(self):
        """Test with positive verbosity bias."""
        replies = ["Hi", "Hello there", "Hi how are you today"]
        human = [3.0, 3.0, 3.0]
        llm = [2.0, 3.0, 4.0]
        result = calculate_length_bias_analysis(replies, human, llm)
        assert "error" not in result
        # LLM scores increase with length while human stays constant

    def test_empty_input(self):
        """Test with empty input."""
        result = calculate_length_bias_analysis([], [], [])
        assert "error" in result

    def test_mismatched_lengths(self):
        """Test with mismatched input lengths."""
        result = calculate_length_bias_analysis(["a", "b"], [3.0], [3.0])
        assert "error" in result
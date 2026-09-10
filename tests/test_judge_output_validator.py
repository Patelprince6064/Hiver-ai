"""Tests for judge output validator."""

import pytest
from src.evaluation.judge.output_validator import (
    validate_judge_output,
    recalculate_overall,
)


class TestValidateJudgeOutput:
    """Tests for output validation."""

    def test_valid_output(self):
        """Test valid output passes validation."""
        data = {
            "relevance": 4,
            "groundedness": 5,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
            "failure_tags": [],
            "short_rationale": "Good reply.",
        }
        is_valid, errors = validate_judge_output(data)
        assert is_valid
        assert len(errors) == 0

    def test_missing_dimension(self):
        """Test that missing dimension is caught."""
        data = {
            "relevance": 4,
            # Missing groundedness
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
        }
        is_valid, errors = validate_judge_output(data)
        assert not is_valid
        assert any("groundedness" in e for e in errors)

    def test_invalid_score_range(self):
        """Test that invalid score range is caught."""
        data = {
            "relevance": 6,  # Invalid
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
        }
        is_valid, errors = validate_judge_output(data)
        assert not is_valid
        assert any("relevance" in e for e in errors)

    def test_invalid_score_type(self):
        """Test that invalid score type is caught."""
        data = {
            "relevance": "high",  # Invalid type
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
        }
        is_valid, errors = validate_judge_output(data)
        assert not is_valid

    def test_invalid_failure_tag(self):
        """Test that invalid failure tag is caught."""
        data = {
            "relevance": 4,
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
            "failure_tags": ["invalid_tag"],
        }
        is_valid, errors = validate_judge_output(data)
        assert not is_valid
        assert any("invalid_tag" in e for e in errors)

    def test_valid_failure_tags(self):
        """Test that valid failure tags pass."""
        data = {
            "relevance": 4,
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
            "failure_tags": ["unsupported_claim", "wrong_intent"],
        }
        is_valid, errors = validate_judge_output(data)
        assert is_valid

    def test_long_rationale(self):
        """Test that overly long rationale is caught."""
        data = {
            "relevance": 4,
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 3,
            "style": 5,
            "short_rationale": "x" * 501,  # Too long
        }
        is_valid, errors = validate_judge_output(data)
        assert not is_valid
        assert any("short_rationale" in e for e in errors)


class TestRecalculateOverall:
    """Tests for overall score recalculation."""

    def test_correct_calculation(self):
        """Test that overall is calculated correctly."""
        scores = {
            "relevance": 4,
            "groundedness": 4,
            "correctness": 4,
            "helpfulness": 4,
            "completeness": 4,
            "style": 4,
        }
        assert recalculate_overall(scores) == 4.0

    def test_different_scores(self):
        """Test with different scores."""
        scores = {
            "relevance": 5,
            "groundedness": 4,
            "correctness": 3,
            "helpfulness": 4,
            "completeness": 5,
            "style": 4,
        }
        expected = (5 + 4 + 3 + 4 + 5 + 4) / 6
        assert recalculate_overall(scores) == round(expected, 2)

    def test_missing_dimension(self):
        """Test with missing dimension uses only available."""
        scores = {
            "relevance": 4,
            "groundedness": 4,
            # Missing others
        }
        # Should use only available scores
        assert recalculate_overall(scores) == 4.0

    def test_invalid_scores_excluded(self):
        """Test that invalid scores are excluded."""
        scores = {
            "relevance": 4,
            "groundedness": 6,  # Invalid, should be excluded
            "correctness": 4,
        }
        # Should only use relevance and correctness
        assert recalculate_overall(scores) == 4.0
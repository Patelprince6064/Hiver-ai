"""Tests for mock judge."""

import pytest
from src.evaluation.judge.mock_judge import MockJudge
from src.evaluation.judge_schema import JudgeInput


class TestMockJudge:
    """Tests for MockJudge implementation."""

    def test_mock_judge_creation(self):
        """Test mock judge creation."""
        judge = MockJudge(seed=42)
        assert judge.seed == 42
        assert judge._call_count == 0

    def test_evaluate_returns_result(self):
        """Test that evaluation returns a result."""
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="I want to return this item.",
            candidate_reply="You can return within 30 days.",
        )
        result = judge.evaluate(judge_input)
        assert result is not None
        assert result.judge_item_id == "test_001"
        assert result.judge_status == "SUCCESS"

    def test_deterministic_output(self):
        """Test that output is deterministic for same input."""
        judge1 = MockJudge(seed=42)
        judge2 = MockJudge(seed=42)
        
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        
        result1 = judge1.evaluate(judge_input)
        result2 = judge2.evaluate(judge_input)
        
        assert result1.relevance == result2.relevance
        assert result1.groundedness == result2.groundedness
        assert result1.overall == result2.overall

    def test_scores_in_range(self):
        """Test that scores are in valid range (1-5)."""
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        result = judge.evaluate(judge_input)
        
        assert 1 <= result.relevance <= 5
        assert 1 <= result.groundedness <= 5
        assert 1 <= result.correctness <= 5
        assert 1 <= result.helpfulness <= 5
        assert 1 <= result.completeness <= 5
        assert 1 <= result.style <= 5
        assert 1.0 <= result.overall <= 5.0

    def test_failure_tags_valid(self):
        """Test that failure tags are valid."""
        from src.evaluation.judge_schema import FAILURE_TAGS
        
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        result = judge.evaluate(judge_input)
        
        for tag in result.failure_tags:
            assert tag in FAILURE_TAGS

    def test_call_count_increments(self):
        """Test that call count increments."""
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        
        assert judge._call_count == 0
        judge.evaluate(judge_input)
        assert judge._call_count == 1
        judge.evaluate(judge_input)
        assert judge._call_count == 2

    def test_invalid_input_returns_error(self):
        """Test that invalid input returns error result."""
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="",  # Empty
            candidate_reply="Test reply",
        )
        result = judge.evaluate(judge_input)
        assert result.judge_status == "ERROR"

    def test_get_stats(self):
        """Test get_stats returns information."""
        judge = MockJudge(seed=42)
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        judge.evaluate(judge_input)
        
        stats = judge.get_stats()
        assert "model" in stats
        assert "call_count" in stats
        assert stats["call_count"] == 1
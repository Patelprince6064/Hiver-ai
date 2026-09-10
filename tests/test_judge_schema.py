"""Tests for judge schema."""

import pytest
from src.evaluation.judge_schema import (
    JudgeInput,
    JudgeResult,
    BlindMapping,
    JudgeEvaluationBatch,
    JudgeReliabilityResult,
    FAILURE_TAGS,
    validate_failure_tags,
)


class TestJudgeInput:
    """Tests for JudgeInput schema."""

    def test_valid_input(self):
        """Test valid judge input creation."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="I want to return this item.",
            intent="return",
            intent_confidence=0.85,
            evidence=[{"text": "Return policy: 30 days", "score": 0.9}],
            candidate_reply="You can return within 30 days.",
        )
        assert judge_input.judge_item_id == "test_001"
        assert judge_input.customer_message == "I want to return this item."
        assert judge_input.intent == "return"
        assert len(judge_input.evidence) == 1

    def test_input_is_frozen(self):
        """Test that input is immutable."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        with pytest.raises(Exception):
            judge_input.customer_message = "Changed message"

    def test_optional_fields(self):
        """Test that optional fields have defaults."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        assert judge_input.conversation_context == ""
        assert judge_input.intent == ""
        assert judge_input.intent_confidence is None
        assert judge_input.evidence == []


class TestJudgeResult:
    """Tests for JudgeResult schema."""

    def test_valid_result(self):
        """Test valid judge result creation."""
        result = JudgeResult(
            judge_item_id="test_001",
            relevance=4,
            groundedness=5,
            correctness=4,
            helpfulness=4,
            completeness=3,
            style=5,
            overall=4.17,
            failure_tags=[],
            short_rationale="Good reply.",
            judge_status="SUCCESS",
            judge_model="test-model",
        )
        assert result.judge_item_id == "test_001"
        assert result.relevance == 4
        assert result.overall == 4.17

    def test_computed_overall(self):
        """Test that computed_overall calculates correctly."""
        result = JudgeResult(
            judge_item_id="test_001",
            relevance=4,
            groundedness=4,
            correctness=4,
            helpfulness=4,
            completeness=4,
            style=4,
            overall=1.0,  # Minimum valid value, will be overridden by computed_overall
            failure_tags=[],
            short_rationale="Test.",
            judge_status="SUCCESS",
            judge_model="test-model",
        )
        assert result.computed_overall == 4.0

    def test_score_validation(self):
        """Test that scores must be 1-5."""
        with pytest.raises(Exception):
            JudgeResult(
                judge_item_id="test_001",
                relevance=6,  # Invalid
                groundedness=4,
                correctness=4,
                helpfulness=4,
                completeness=4,
                style=4,
                overall=4.0,
                failure_tags=[],
                short_rationale="Test.",
                judge_status="SUCCESS",
                judge_model="test-model",
            )


class TestBlindMapping:
    """Tests for BlindMapping schema."""

    def test_valid_mapping(self):
        """Test valid blind mapping creation."""
        mapping = BlindMapping(
            judge_item_id="test_001_A",
            candidate_id="A",
            system_name="grounded_llm_verified",
            seed=42,
        )
        assert mapping.candidate_id == "A"
        assert mapping.system_name == "grounded_llm_verified"


class TestFailureTags:
    """Tests for failure tags."""

    def test_valid_tags(self):
        """Test that valid tags are accepted."""
        assert validate_failure_tags(["unsupported_claim", "wrong_intent"])
        assert validate_failure_tags([])
        assert validate_failure_tags(["other"])

    def test_invalid_tags(self):
        """Test that invalid tags are rejected."""
        assert not validate_failure_tags(["invalid_tag"])
        assert not validate_failure_tags(["unsupported_claim", "nonexistent"])

    def test_all_tags_defined(self):
        """Test that all expected tags are defined."""
        expected_tags = {
            "unsupported_claim", "wrong_intent", "wrong_resolution",
            "missing_context", "too_generic", "unhelpful", "incomplete",
            "historical_customer_info", "unsupported_timeline", "unsupported_price",
            "unsupported_policy", "awkward_style", "too_verbose", "too_short",
            "retrieval_error", "insufficient_evidence", "other",
        }
        assert expected_tags == FAILURE_TAGS
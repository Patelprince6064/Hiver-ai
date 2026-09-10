"""Tests for judge prompt."""

import pytest
from src.evaluation.llm_judge_prompt import (
    JUDGE_SYSTEM_PROMPT,
    build_judge_prompt,
    build_judge_messages,
    validate_prompt_safety,
    PROHIBITED_TERMS,
)
from src.evaluation.judge_schema import JudgeInput


class TestJudgePrompt:
    """Tests for judge prompt construction."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert JUDGE_SYSTEM_PROMPT is not None
        assert len(JUDGE_SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_dimensions(self):
        """Test that system prompt contains all dimensions."""
        dimensions = ["RELEVANCE", "GROUNDEDNESS", "CORRECTNESS", "HELPFULNESS", "COMPLETENESS", "STYLE"]
        for dim in dimensions:
            assert dim in JUDGE_SYSTEM_PROMPT

    def test_build_judge_prompt(self):
        """Test prompt building from input."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="I want to return this item.",
            intent="return",
            candidate_reply="You can return within 30 days.",
        )
        prompt = build_judge_prompt(judge_input)
        assert "I want to return this item." in prompt
        assert "You can return within 30 days." in prompt
        assert "return" in prompt

    def test_build_judge_messages(self):
        """Test message array building."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        messages = build_judge_messages(judge_input)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test message" in messages[1]["content"]
        assert "Test reply" in messages[1]["content"]

    def test_evidence_in_prompt(self):
        """Test that evidence is included in prompt."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test",
            evidence=[{"text": "Return policy: 30 days"}],
            candidate_reply="Test reply",
        )
        prompt = build_judge_prompt(judge_input)
        assert "Return policy: 30 days" in prompt

    def test_no_evidence_in_prompt(self):
        """Test prompt without evidence."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test",
            evidence=[],
            candidate_reply="Test reply",
        )
        prompt = build_judge_prompt(judge_input)
        assert "No evidence provided" in prompt


class TestPromptSafety:
    """Tests for prompt safety validation."""

    def test_safe_prompt(self):
        """Test that safe prompt passes validation."""
        judge_input = JudgeInput(
            judge_item_id="test_001",
            customer_message="Test message",
            candidate_reply="Test reply",
        )
        prompt = build_judge_prompt(judge_input)
        is_safe, violations = validate_prompt_safety(prompt)
        assert is_safe
        assert len(violations) == 0

    def test_prohibited_terms(self):
        """Test that prohibited terms are detected."""
        for term in PROHIBITED_TERMS[:5]:  # Test first 5
            is_safe, violations = validate_prompt_safety(f"This contains {term}")
            assert not is_safe
            assert any(term in v for v in violations)

    def test_case_insensitive(self):
        """Test that detection is case-insensitive."""
        is_safe, violations = validate_prompt_safety("This contains SYSTEM_NAME")
        assert not is_safe
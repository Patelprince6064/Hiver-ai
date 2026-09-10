"""Tests for final judge blindness audit."""

import pytest
import json


def audit_blindness(inputs: list[dict]) -> dict:
    """Audit judge inputs for blindness.

    Args:
        inputs: List of judge input items.

    Returns:
        Blindness audit results.
    """
    prohibited_terms = [
        "system_name",
        "model_name",
        "provider",
        "human_score",
        "expected_score",
        "ground_truth",
        "gold_label",
        "baseline",
        "final_system",
        "openai",
        "anthropic",
        "google",
        "gpt-",
        "claude",
        "gemini",
        "generic_baseline",
        "historical_baseline",
        "grounded_llm",
        "grounded_llm_verified",
    ]

    violations = []
    items_audited = 0

    for item in inputs:
        items_audited += 1
        item_id = item.get("judge_item_id", "unknown")

        # Convert to string for text search
        item_text = json.dumps(item).lower()

        item_violations = []
        for term in prohibited_terms:
            if term.lower() in item_text:
                item_violations.append(term)

        if item_violations:
            violations.append({
                "judge_item_id": item_id,
                "violations": item_violations,
            })

    return {
        "items_audited": items_audited,
        "items_with_violations": len(violations),
        "violations": violations,
        "is_blind": len(violations) == 0,
    }


class TestFinalBlindnessAudit:
    """Tests for final blindness audit."""

    def test_blind_input(self):
        """Test with blind input."""
        inputs = [
            {
                "judge_item_id": "eval_0001_A",
                "customer_message": "I want to return this item.",
                "candidate_reply": "You can return within 30 days.",
            }
        ]
        result = audit_blindness(inputs)
        assert result["is_blind"] is True
        assert result["items_with_violations"] == 0

    def test_system_name_leakage(self):
        """Test detection of system name leakage."""
        inputs = [
            {
                "judge_item_id": "eval_0001_A",
                "customer_message": "I want to return this item.",
                "candidate_reply": "You can return within 30 days.",
                "system_name": "grounded_llm_verified",
            }
        ]
        result = audit_blindness(inputs)
        assert result["is_blind"] is False
        assert result["items_with_violations"] == 1

    def test_human_score_leakage(self):
        """Test detection of human score leakage."""
        inputs = [
            {
                "judge_item_id": "eval_0001_A",
                "customer_message": "I want to return this item.",
                "candidate_reply": "You can return within 30 days.",
                "human_score": 4.5,
            }
        ]
        result = audit_blindness(inputs)
        assert result["is_blind"] is False

    def test_model_name_leakage(self):
        """Test detection of model name leakage."""
        inputs = [
            {
                "judge_item_id": "eval_0001_A",
                "customer_message": "I want to return this item.",
                "candidate_reply": "You can return within 30 days.",
                "model": "gpt-4",
            }
        ]
        result = audit_blindness(inputs)
        assert result["is_blind"] is False

    def test_empty_input(self):
        """Test with empty input."""
        result = audit_blindness([])
        assert result["items_audited"] == 0
        assert result["is_blind"] is True
"""Tests for context budget."""

import pytest
from src.generation.context_budget import ContextBudget


class TestContextBudget:
    def test_fit_customer_message_short(self):
        budget = ContextBudget(max_customer_message_chars=100)
        msg = "Hello"
        assert budget.fit_customer_message(msg) == "Hello"

    def test_fit_customer_message_long(self):
        budget = ContextBudget(max_customer_message_chars=10)
        msg = "This is a very long customer message"
        result = budget.fit_customer_message(msg)
        assert len(result) == 13  # 10 + "..."
        assert result.endswith("...")

    def test_fit_evidence_within_budget(self):
        budget = ContextBudget(max_total_evidence_chars=1000)
        evidence = [
            {"support_response": "Short reply", "customer_message": "Short msg"},
        ]
        fitted = budget.fit_evidence(evidence)
        assert len(fitted) == 1

    def test_fit_evidence_truncates_long_items(self):
        budget = ContextBudget(max_evidence_item_chars=10)
        evidence = [
            {"support_response": "A very long support response that exceeds limit", "customer_message": "Hi"},
        ]
        fitted = budget.fit_evidence(evidence)
        assert len(fitted[0]["support_response"]) <= 13  # 10 + "..."

    def test_fit_evidence_total_budget(self):
        budget = ContextBudget(max_total_evidence_chars=50, max_evidence_item_chars=100)
        evidence = [
            {"support_response": "A" * 20, "customer_message": "B" * 20},
            {"support_response": "C" * 20, "customer_message": "D" * 20},
        ]
        fitted = budget.fit_evidence(evidence)
        assert len(fitted) == 1  # Only first fits within 50 chars total

    def test_get_params(self):
        budget = ContextBudget(max_customer_message_chars=200)
        params = budget.get_params()
        assert params["max_customer_message_chars"] == 200

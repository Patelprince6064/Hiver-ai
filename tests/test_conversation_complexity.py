"""Tests for conversation_complexity.py — Conversation complexity signals."""

import pytest
from src.escalation.conversation_complexity import (
    ConversationComplexity,
    compute_conversation_complexity,
    complexity_to_dict,
)


class TestConversationComplexity:
    def test_no_history(self):
        complexity = compute_conversation_complexity(
            current_message="Hello, I need help"
        )
        assert complexity.num_turns == 0
        assert complexity.num_customer_messages == 1
        assert complexity.complexity_level == "low"

    def test_simple_conversation(self):
        history = [
            {"role": "customer", "text": "Where is my order?"},
            {"role": "support", "text": "Please provide your order number."},
        ]
        complexity = compute_conversation_complexity(
            conversation_history=history,
            current_message="Thanks, it's 12345",
        )
        assert complexity.num_turns == 2
        assert complexity.num_customer_messages == 1
        assert complexity.num_support_responses == 1

    def test_repeated_request(self):
        history = [
            {"role": "customer", "text": "Where is my order?"},
            {"role": "support", "text": "Checking..."},
            {"role": "customer", "text": "Where is my order?"},
            {"role": "support", "text": "Still checking..."},
            {"role": "customer", "text": "Where is my order?"},
        ]
        complexity = compute_conversation_complexity(
            conversation_history=history,
            current_message="I'm still waiting",
        )
        assert complexity.has_repeated_request is True

    def test_multiple_intents(self):
        history = [
            {"role": "customer", "text": "I need help with billing and shipping"},
        ]
        complexity = compute_conversation_complexity(
            conversation_history=history,
            current_message="Also, check my order status",
            detected_intents=["billing_issue", "shipping_info", "order_status"],
        )
        assert complexity.has_multiple_intents is True

    def test_contradictory_requests(self):
        history = [
            {"role": "customer", "text": "Cancel my order but keep my subscription"},
        ]
        complexity = compute_conversation_complexity(
            conversation_history=history,
            current_message="I changed my mind",
        )
        assert complexity.has_contradictory_requests is True

    def test_unresolved_prior_turns(self):
        history = [
            {"role": "customer", "text": "My order is late"},
            {"role": "support", "text": "We're looking into it."},
            {"role": "customer", "text": "Still waiting"},
            {"role": "support", "text": "We're checking with the carrier."},
        ]
        complexity = compute_conversation_complexity(
            conversation_history=history,
            current_message="Any updates?",
        )
        assert complexity.has_unresolved_prior_turns is True

    def test_complexity_score_increases_with_turns(self):
        short_history = [
            {"role": "customer", "text": "Hello"},
            {"role": "support", "text": "Hi"},
        ]
        long_history = short_history * 5

        short_complexity = compute_conversation_complexity(
            conversation_history=short_history,
            current_message="Help",
        )
        long_complexity = compute_conversation_complexity(
            conversation_history=long_history,
            current_message="Help",
        )
        assert long_complexity.complexity_score > short_complexity.complexity_score

    def test_complexity_to_dict(self):
        complexity = compute_conversation_complexity(
            current_message="Hello"
        )
        d = complexity_to_dict(complexity)
        assert isinstance(d, dict)
        assert "num_turns" in d
        assert "complexity_score" in d
        assert "complexity_level" in d

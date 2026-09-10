"""Tests for prompt builder."""

import pytest
from src.generation.prompt_builder import GroundedReplyPromptBuilder, SYSTEM_PROMPT


class TestGroundedReplyPromptBuilder:
    def test_build_basic(self):
        builder = GroundedReplyPromptBuilder()
        prompt = builder.build(
            customer_message="My order is late",
            predicted_intent="delivery_delay",
            intent_confidence=0.91,
            evidence=[],
        )
        assert "My order is late" in prompt
        assert "delivery_delay" in prompt
        assert "0.91" in prompt
        assert "INSUFFICIENT_EVIDENCE" in prompt

    def test_build_with_evidence(self):
        builder = GroundedReplyPromptBuilder()
        evidence = [
            {
                "knowledge_id": "kb_001",
                "similarity_score": 0.89,
                "intent": "delivery_delay",
                "resolution_type": "requested_information",
                "customer_message": "My package is missing",
                "support_response": "DM us your order number.",
            }
        ]
        prompt = builder.build(
            customer_message="My order is late",
            predicted_intent="delivery_delay",
            evidence=evidence,
        )
        assert "kb_001" not in prompt  # ID should not appear in prompt text
        assert "DM us your order number" in prompt
        assert "My package is missing" in prompt
        assert "delivery_delay" in prompt

    def test_build_no_evidence(self):
        builder = GroundedReplyPromptBuilder()
        prompt = builder.build(
            customer_message="Help me",
            evidence=[],
        )
        assert "None available" in prompt

    def test_system_prompt(self):
        builder = GroundedReplyBuilder()
        assert "customer-support" in builder.get_system_prompt().lower()

    def test_custom_system_prompt(self):
        custom = "Custom system prompt."
        builder = GroundedReplyPromptBuilder(system_prompt=custom)
        assert builder.get_system_prompt() == custom

    def test_evidence_section_header(self):
        builder = GroundedReplyPromptBuilder()
        evidence = [
            {
                "similarity_score": 0.8,
                "intent": "billing",
                "resolution_type": "troubleshooting",
                "customer_message": "Help",
                "support_response": "Call us.",
            }
        ]
        prompt = builder.build(customer_message="Hi", evidence=evidence)
        assert "HISTORICAL SUPPORT EVIDENCE" in prompt
        assert "Call us." in prompt


class TestGroundedReplyBuilder:
    pass


# Alias for backward compat
GroundedReplyBuilder = GroundedReplyPromptBuilder

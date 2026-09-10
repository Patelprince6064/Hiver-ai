"""Tests for agent schema."""

import pytest
from src.agent.agent_schema import (
    AgentEvidence,
    AgentEscalation,
    AgentRequest,
    AgentResponse,
    HumanReviewPackage,
    build_agent_response,
)


class TestAgentRequest:
    def test_valid_request(self):
        request = AgentRequest(message="Where is my order?")
        assert request.message == "Where is my order?"
        assert request.conversation_id is None
        assert request.message_id is None
        assert request.conversation_context == []

    def test_request_with_context(self):
        request = AgentRequest(
            message="test",
            conversation_id="conv_001",
            message_id="msg_001",
            conversation_context=[{"role": "customer", "content": "hi"}],
        )
        assert request.conversation_id == "conv_001"
        assert len(request.conversation_context) == 1

    def test_request_minimal(self):
        request = AgentRequest(message="test message")
        assert request.message == "test message"


class TestAgentResponse:
    def test_auto_handle_response(self):
        response = build_agent_response(
            decision="AUTO_HANDLE",
            reply="Your order is on the way.",
            intent="order_status",
            intent_confidence=0.85,
            grounding_status="pass",
            escalation_decision="AUTO_HANDLE",
            trace_id="trace_001",
        )
        assert response.decision == "AUTO_HANDLE"
        assert response.reply == "Your order is on the way."
        assert response.intent == "order_status"
        assert response.human_review is None

    def test_escalation_response(self):
        response = build_agent_response(
            decision="ESCALATE_TO_HUMAN",
            escalation_decision="ESCALATE_TO_HUMAN",
            escalation_reason_codes=["LOW_INTENT_CONFIDENCE"],
            escalation_risk_level="MEDIUM",
            human_review={
                "customer_message": "test",
                "escalation_reasons": ["LOW_INTENT_CONFIDENCE"],
            },
            trace_id="trace_002",
        )
        assert response.decision == "ESCALATE_TO_HUMAN"
        assert response.reply is None
        assert response.human_review is not None
        assert response.escalation.reason_codes == ["LOW_INTENT_CONFIDENCE"]


class TestAgentEvidence:
    def test_evidence_creation(self):
        evidence = AgentEvidence(
            knowledge_id="KB001",
            customer_message="Where is my order?",
            support_response="Your order is on the way.",
            similarity_score=0.75,
            intent="order_status",
            resolution_type="information_provided",
        )
        assert evidence.knowledge_id == "KB001"
        assert evidence.similarity_score == 0.75


class TestAgentEscalation:
    def test_escalation_creation(self):
        escalation = AgentEscalation(
            decision="ESCALATE_TO_HUMAN",
            reason_codes=["LOW_INTENT_CONFIDENCE"],
            risk_level="MEDIUM",
            policy_version="v1.1",
        )
        assert escalation.decision == "ESCALATE_TO_HUMAN"
        assert escalation.policy_version == "v1.1"


class TestHumanReviewPackage:
    def test_review_package(self):
        package = HumanReviewPackage(
            customer_message="I need help",
            predicted_intent="general_inquiry",
            intent_confidence=0.45,
            escalation_reasons=["LOW_INTENT_CONFIDENCE"],
            recommended_action="Review conversation and respond manually.",
        )
        assert package.customer_message == "I need help"
        assert package.intent_confidence == 0.45
        assert "UNSENT" not in package.customer_message

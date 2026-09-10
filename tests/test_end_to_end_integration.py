"""End-to-end integration tests."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import SupportAgent, create_agent
from src.generation.reply_schema import build_reply_output
from src.retrieval.retrieval_schema import RetrievalResponse, RetrievalResult


class TestEndToEndIntegration:
    """Test complete pipeline integration."""

    def test_case_a_safe_evidence_backed(self):
        """CASE A: Safe evidence-backed request -> AUTO_HANDLE."""
        agent = create_agent(mock_mode=True)
        request = AgentRequest(
            message="Where is my order? I placed it 3 days ago.",
            conversation_id="conv_001",
        )
        response = agent.process(request)

        assert response.decision == "AUTO_HANDLE"
        assert response.reply is not None
        assert response.intent == "order_status"
        assert response.intent_confidence == 0.85
        assert response.grounding_status == "pass"
        assert response.escalation.decision == "AUTO_HANDLE"
        assert response.trace_id is not None
        assert response.human_review is None

    def test_case_b_insufficient_evidence(self):
        """CASE B: Insufficient evidence -> ESCALATE_TO_HUMAN."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = RetrievalResponse(
            query="test",
            retrieval_status="insufficient_evidence",
            results=[],
        )
        agent = create_agent(mock_mode=True, retriever=mock_retriever)
        request = AgentRequest(message="What is your policy on quantum computing returns?")
        response = agent.process(request)

        assert response.decision == "ESCALATE_TO_HUMAN"
        assert response.reply is None
        assert response.human_review is not None

    def test_case_c_grounding_failure(self):
        """CASE C: Grounding failure -> ESCALATE_TO_HUMAN."""
        with patch("src.agent.support_agent.run_grounding_checks") as mock_grounding:
            mock_grounding.return_value = MagicMock(
                passed=False,
                checks={"evidence_presence": True, "historical_phrase_overlap": False},
                issues=["Low evidence overlap: 0.05"],
            )
            agent = create_agent(mock_mode=True)
            request = AgentRequest(message="test message")
            response = agent.process(request)

            assert response.decision == "ESCALATE_TO_HUMAN"

    def test_case_d_low_intent_confidence(self):
        """CASE D: Low intent confidence -> ESCALATE_TO_HUMAN."""
        mock_classifier = MagicMock()
        mock_classifier.predict_with_confidence.return_value = [
            {
                "intent": "unknown",
                "confidence": 0.30,
                "probabilities": {"unknown": 0.30, "other": 0.25, "general": 0.25, "misc": 0.20},
            }
        ]
        agent = create_agent(mock_mode=True, classifier=mock_classifier)
        request = AgentRequest(message="asdfghjkl qwerty")
        response = agent.process(request)

        assert response.decision == "ESCALATE_TO_HUMAN"
        assert response.human_review is not None

    def test_case_e_account_specific_action(self):
        """CASE E: External/account-specific action -> ESCALATE_TO_HUMAN.

        Account actions always escalate because the agent cannot perform
        external account modifications.
        """
        from src.escalation.decision_engine import EscalationDecisionEngine
        from src.escalation.rule_based_policy import RiskAwarePolicy

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = RetrievalResponse(
            query="test",
            retrieval_status="success",
            results=[
                RetrievalResult(
                    rank=1,
                    knowledge_id="KB001",
                    customer_message="test",
                    support_response="Please contact support for account changes.",
                    similarity_score=0.80,
                )
            ],
        )

        mock_generator = MagicMock()
        mock_generator.generate.return_value = build_reply_output(
            query="test",
            reply="I can help you delete your account. Please confirm.",
            generation_method="grounded_llm",
            status="success",
            predicted_intent="account_action",
            intent_confidence=0.85,
            risk_flags=["account_action_required"],
        )

        agent = create_agent(mock_mode=True, retriever=mock_retriever, generator=mock_generator)
        request = AgentRequest(message="I want to delete my account")
        response = agent.process(request)

        assert response.decision == "ESCALATE_TO_HUMAN"
        assert response.human_review is not None

    def test_full_pipeline_trace_preserved(self):
        """Test that trace is preserved through the full pipeline."""
        agent = create_agent(mock_mode=True)
        request = AgentRequest(
            message="Where is my order?",
            conversation_id="conv_trace",
            message_id="msg_trace",
        )
        response = agent.process(request)

        assert response.trace_id is not None
        assert response.metadata.get("policy_version") == "v1.1"

    def test_auto_handle_has_no_human_review(self):
        """AUTO_HANDLE responses should not have human_review."""
        agent = create_agent(mock_mode=True)
        request = AgentRequest(message="Where is my order?")
        response = agent.process(request)

        if response.decision == "AUTO_HANDLE":
            assert response.human_review is None
            assert response.reply is not None

    def test_escalation_has_human_review(self):
        """ESCALATE_TO_HUMAN responses should have human_review."""
        mock_classifier = MagicMock()
        mock_classifier.predict_with_confidence.side_effect = Exception("fail")
        agent = create_agent(mock_mode=True, classifier=mock_classifier)
        request = AgentRequest(message="test")
        response = agent.process(request)

        assert response.decision == "ESCALATE_TO_HUMAN"
        assert response.human_review is not None
        assert response.human_review.customer_message == "test"

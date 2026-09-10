"""Tests for agent failure modes."""

import pytest
from unittest.mock import MagicMock, patch

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import SupportAgent, create_agent


class TestAgentFailureModes:
    def test_intent_failure_escalates(self):
        mock_classifier = MagicMock()
        mock_classifier.predict_with_confidence.side_effect = Exception("Classifier failed")
        agent = create_agent(mock_mode=True, classifier=mock_classifier)
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

    def test_retrieval_failure_escalates(self):
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("Retrieval failed")
        agent = create_agent(mock_mode=True, retriever=mock_retriever)
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

    def test_generation_failure_escalates(self):
        mock_generator = MagicMock()
        mock_generator.generate.side_effect = Exception("Generation failed")
        agent = create_agent(mock_mode=True, generator=mock_generator)
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

    def test_grounding_failure_escalates(self):
        with patch("src.agent.support_agent.run_grounding_checks") as mock_grounding:
            mock_grounding.side_effect = Exception("Grounding failed")
            agent = create_agent(mock_mode=True)
            request = AgentRequest(message="test")
            response = agent.process(request)
            assert response.decision == "ESCALATE_TO_HUMAN"

    def test_escalation_engine_failure_escalates(self):
        agent = create_agent(mock_mode=True)
        with patch.object(agent.escalation_engine, "evaluate") as mock_eval:
            mock_eval.side_effect = Exception("Escalation failed")
            request = AgentRequest(message="test")
            response = agent.process(request)
            assert response.decision == "ESCALATE_TO_HUMAN"

    def test_no_components_escalates(self):
        agent = SupportAgent(
            classifier=None,
            retriever=None,
            generator=None,
            mock_mode=False,
        )
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

    def test_insufficient_evidence_escalates(self):
        from unittest.mock import MagicMock
        from src.retrieval.retrieval_schema import RetrievalResponse

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = RetrievalResponse(
            query="test",
            retrieval_status="insufficient_evidence",
            results=[],
        )
        agent = create_agent(mock_mode=True, retriever=mock_retriever)
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

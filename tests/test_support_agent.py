"""Tests for the support agent."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import SupportAgent, create_agent
from src.generation.reply_schema import build_reply_output
from src.retrieval.retrieval_schema import RetrievalResponse, RetrievalResult
from src.escalation.escalation_schema import build_escalation_decision


class TestSupportAgent:
    def test_mock_agent_creation(self):
        agent = create_agent(mock_mode=True)
        assert agent.mock_mode is True
        assert agent.classifier is not None
        assert agent.retriever is not None
        assert agent.generator is not None

    def test_mock_agent_processes_request(self):
        agent = create_agent(mock_mode=True)
        request = AgentRequest(message="Where is my order?")
        response = agent.process(request)
        assert response.decision in ("AUTO_HANDLE", "ESCALATE_TO_HUMAN")
        assert response.trace_id is not None

    def test_mock_agent_auto_handle(self):
        agent = create_agent(mock_mode=True)
        request = AgentRequest(message="Where is my order?")
        response = agent.process(request)
        assert response.decision == "AUTO_HANDLE"
        assert response.reply is not None
        assert response.intent == "order_status"

    def test_agent_with_mock_classifier(self):
        mock_classifier = MagicMock()
        mock_classifier.predict_with_confidence.return_value = [
            {
                "intent": "return",
                "confidence": 0.90,
                "probabilities": {"return": 0.90, "order_status": 0.10},
            }
        ]
        agent = create_agent(mock_mode=True, classifier=mock_classifier)
        request = AgentRequest(message="I want to return an item")
        response = agent.process(request)
        assert response.intent == "return"

    def test_agent_with_mock_retriever(self):
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = RetrievalResponse(
            query="test",
            retrieval_status="success",
            results=[
                RetrievalResult(
                    rank=1,
                    knowledge_id="KB001",
                    customer_message="test",
                    support_response="test response",
                    similarity_score=0.80,
                )
            ],
        )
        agent = create_agent(mock_mode=True, retriever=mock_retriever)
        request = AgentRequest(message="test message")
        response = agent.process(request)
        assert len(response.evidence) > 0

    def test_agent_with_mock_generator(self):
        mock_generator = MagicMock()
        mock_generator.generate.return_value = build_reply_output(
            query="test",
            reply="This is a test reply.",
            generation_method="grounded_llm",
            status="success",
            predicted_intent="order_status",
            intent_confidence=0.85,
        )
        agent = create_agent(mock_mode=True, generator=mock_generator)
        request = AgentRequest(message="Where is my order?")
        response = agent.process(request)
        assert response.reply == "This is a test reply."

    def test_agent_empty_message(self):
        agent = create_agent(mock_mode=True)
        request = AgentRequest(message="")
        response = agent.process(request)
        assert response.decision == "ESCALATE_TO_HUMAN"

    def test_agent_preserves_trace(self):
        agent = create_agent(mock_mode=True)
        request = AgentRequest(message="test")
        response = agent.process(request)
        assert response.trace_id is not None
        assert len(response.trace_id) > 0

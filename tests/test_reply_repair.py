"""Tests for reply_repair module."""

import pytest
from unittest.mock import MagicMock
from src.generation.reply_repair import ReplyRepairer
from src.generation.llm.base_provider import LLMResponse
from src.generation.reply_schema import ReplyOutput


@pytest.fixture
def mock_llm():
    provider = MagicMock()
    provider.get_params.return_value = {"model": "mock"}
    return provider


@pytest.fixture
def sample_evidence():
    return [
        {
            "knowledge_id": "KB-001",
            "customer_message": "My order hasn't arrived.",
            "support_response": "We have forwarded your request to the logistics team.",
            "intent": "shipping",
            "resolution_type": "investigation",
        },
    ]


class TestReplyRepairer:
    def test_successful_repair(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(
            text="We have forwarded your request to the logistics team. Please DM us your order number.",
            status="success",
        )
        repairer = ReplyRepairer(llm_provider=mock_llm)
        result = repairer.repair(
            customer_message="Where is my order?",
            original_reply="Your order will arrive in 2 days.",
            evidence=sample_evidence,
            unsupported_claims=[{"claim": "your order will arrive in 2 days", "type": "timeline"}],
        )
        assert isinstance(result, ReplyOutput)
        assert result.status == "success"
        assert result.reply is not None
        assert result.generation_method == "grounded_llm_repair"
        assert result.metadata.get("repair_attempt") is True

    def test_insufficient_evidence_repair(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(
            text="INSUFFICIENT_EVIDENCE",
            status="success",
        )
        repairer = ReplyRepairer(llm_provider=mock_llm)
        result = repairer.repair(
            customer_message="Where is my order?",
            original_reply="Your order will arrive in 2 days.",
            evidence=sample_evidence,
            unsupported_claims=[{"claim": "arrive in 2 days", "type": "timeline"}],
        )
        assert result.status == "insufficient_evidence"

    def test_provider_error(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(
            text="",
            status="error",
            error_type="api_error",
            error_message="Rate limited",
        )
        repairer = ReplyRepairer(llm_provider=mock_llm)
        result = repairer.repair(
            customer_message="Where is my order?",
            original_reply="Your order will arrive in 2 days.",
            evidence=sample_evidence,
            unsupported_claims=[{"claim": "arrive in 2 days", "type": "timeline"}],
        )
        assert result.status == "provider_error"

    def test_empty_reply_repair(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(
            text="",
            status="success",
        )
        repairer = ReplyRepairer(llm_provider=mock_llm)
        result = repairer.repair(
            customer_message="Where is my order?",
            original_reply="Your order will arrive in 2 days.",
            evidence=sample_evidence,
            unsupported_claims=[{"claim": "arrive in 2 days", "type": "timeline"}],
        )
        assert result.status == "insufficient_evidence"

    def test_repair_passes_evidence(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(text="OK", status="success")
        repairer = ReplyRepairer(llm_provider=mock_llm)
        repairer.repair(
            customer_message="Where is my order?",
            original_reply="Test reply.",
            evidence=sample_evidence,
            unsupported_claims=[],
        )
        call_args = mock_llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args[1].get("prompt", ""))
        assert "forwarded your request" in prompt

    def test_repair_passes_unsupported_claims(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(text="OK", status="success")
        repairer = ReplyRepairer(llm_provider=mock_llm)
        unsupported = [{"claim": "will arrive tomorrow", "type": "timeline"}]
        repairer.repair(
            customer_message="Where is my order?",
            original_reply="Test reply.",
            evidence=sample_evidence,
            unsupported_claims=unsupported,
        )
        call_args = mock_llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args[1].get("prompt", ""))
        assert "will arrive tomorrow" in prompt

    def test_get_params(self, mock_llm):
        repairer = ReplyRepairer(llm_provider=mock_llm, max_attempts=2)
        params = repairer.get_params()
        assert params["repairer"] == "ReplyRepairer"
        assert params["max_attempts"] == 2
        assert "temperature" in params
        assert "max_tokens" in params

    def test_repair_metadata(self, mock_llm, sample_evidence):
        mock_llm.generate.return_value = LLMResponse(text="Fixed reply.", status="success")
        repairer = ReplyRepairer(llm_provider=mock_llm)
        result = repairer.repair(
            customer_message="Where is my order?",
            original_reply="Bad reply.",
            evidence=sample_evidence,
            unsupported_claims=[{"claim": "bad claim", "type": "price"}],
        )
        assert result.metadata.get("original_reply") == "Bad reply."
        assert result.metadata.get("n_unsupported_claims") == 1

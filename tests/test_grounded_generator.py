"""Tests for grounded reply generator."""

import pytest
from src.generation.grounded_reply_generator import GroundedReplyGenerator
from src.generation.llm.mock_provider import MockLLMProvider
from src.generation.evidence_selector import EvidenceSelector
from src.retrieval.retrieval_schema import RetrievalResult, RetrievalResponse


class FakeRetriever:
    def __init__(self, results=None, status="success"):
        self._results = results or []
        self._status = status

    def retrieve(self, query, top_k=1, intent=None, min_similarity=None):
        return RetrievalResponse(
            query=query,
            predicted_intent=intent,
            retrieval_status=self._status,
            results=self._results,
        )


def _make_result(
    knowledge_id="kb_001",
    support_response="DM us your order number.",
    score=0.9,
    customer_message="My order is late",
):
    return RetrievalResult(
        rank=1,
        knowledge_id=knowledge_id,
        customer_message=customer_message,
        support_response=support_response,
        similarity_score=score,
    )


class TestGroundedReplyGenerator:
    def test_generate_with_evidence(self):
        result = _make_result()
        retriever = FakeRetriever(results=[result])
        llm = MockLLMProvider(response="Please DM us your order number.")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(
            customer_message="My order is late",
            predicted_intent="delivery_delay",
        )
        assert output.reply == "Please DM us your order number."
        assert output.status == "success"
        assert output.generation_method == "grounded_llm"

    def test_insufficient_evidence_no_retrieval(self):
        retriever = FakeRetriever(results=[], status="insufficient_evidence")
        llm = MockLLMProvider(response="Should not be called")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="Unknown")
        assert output.reply is None
        assert output.status == "insufficient_evidence"

    def test_insufficient_evidence_no_selected(self):
        retriever = FakeRetriever(results=[])
        llm = MockLLMProvider(response="Should not be called")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="Unknown", evidence=[])
        assert output.reply is None
        assert output.status == "insufficient_evidence"

    def test_llm_returns_insufficient_evidence(self):
        result = _make_result()
        retriever = FakeRetriever(results=[result])
        llm = MockLLMProvider(response="INSUFFICIENT_EVIDENCE")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="My order is late")
        assert output.reply is None
        assert output.status == "insufficient_evidence"

    def test_llm_provider_error(self):
        result = _make_result()
        retriever = FakeRetriever(results=[result])
        llm = MockLLMProvider(response="", status="provider_error")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="My order is late")
        assert output.reply is None
        assert output.status == "provider_error"

    def test_evidence_preserved(self):
        result = _make_result(knowledge_id="kb_042", score=0.88)
        retriever = FakeRetriever(results=[result])
        llm = MockLLMProvider(response="Hello!")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="Help")
        assert len(output.evidence) == 1
        assert output.evidence[0].knowledge_id == "kb_042"

    def test_pre_fetched_evidence(self):
        evidence = [
            {
                "knowledge_id": "kb_001",
                "similarity_score": 0.9,
                "support_response": "DM us.",
                "intent": "delivery_delay",
                "resolution_type": "requested_information",
                "customer_message": "Where is my order?",
            }
        ]
        retriever = FakeRetriever()
        llm = MockLLMProvider(response="Please DM us.")
        gen = GroundedReplyGenerator(retriever=retriever, llm_provider=llm)
        output = gen.generate(customer_message="Help", evidence=evidence)
        assert output.reply == "Please DM us."
        assert output.status == "success"

    def test_prompt_version_recorded(self):
        result = _make_result()
        retriever = FakeRetriever(results=[result])
        llm = MockLLMProvider(response="Hello!")
        gen = GroundedReplyGenerator(
            retriever=retriever, llm_provider=llm, prompt_version="v2"
        )
        output = gen.generate(customer_message="Test")
        assert output.metadata.get("prompt_version") == "v2"

    def test_get_params(self):
        retriever = FakeRetriever()
        llm = MockLLMProvider()
        gen = GroundedReplyGenerator(
            retriever=retriever, llm_provider=llm, temperature=0.5
        )
        params = gen.get_params()
        assert params["temperature"] == 0.5
        assert params["generator"] == "GroundedReplyGenerator"

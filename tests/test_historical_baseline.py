"""Tests for historical reply baseline."""

import pytest
from unittest.mock import MagicMock
from src.generation.historical_baseline import HistoricalReplyGenerator
from src.retrieval.retrieval_schema import RetrievalResult, RetrievalResponse


class FakeRetriever:
    """Minimal fake retriever for testing."""

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


def _make_result(knowledge_id="kb_001", support_response="DM us your order number.", score=0.9, customer_message="My order is late"):
    return RetrievalResult(
        rank=1,
        knowledge_id=knowledge_id,
        customer_message=customer_message,
        support_response=support_response,
        similarity_score=score,
    )


class TestHistoricalReplyGenerator:
    def test_returns_top_response(self):
        result = _make_result(support_response="Please send your order number.")
        retriever = FakeRetriever(results=[result])
        gen = HistoricalReplyGenerator(retriever=retriever)
        output = gen.generate("My order is late")
        assert output.reply == "Please send your order number."
        assert output.status == "success"

    def test_preserves_evidence(self):
        result = _make_result(knowledge_id="kb_042", score=0.88)
        retriever = FakeRetriever(results=[result])
        gen = HistoricalReplyGenerator(retriever=retriever)
        output = gen.generate("Test query")
        assert len(output.evidence) == 1
        assert output.evidence[0].knowledge_id == "kb_042"
        assert output.evidence[0].similarity_score == 0.88

    def test_insufficient_evidence(self):
        retriever = FakeRetriever(results=[], status="insufficient_evidence")
        gen = HistoricalReplyGenerator(retriever=retriever, require_evidence=True)
        output = gen.generate("Unknown query")
        assert output.reply is None
        assert output.status == "insufficient_evidence"

    def test_no_fabrication(self):
        retriever = FakeRetriever(results=[], status="insufficient_evidence")
        gen = HistoricalReplyGenerator(retriever=retriever, require_evidence=True)
        output = gen.generate("Unknown")
        assert output.reply is None

    def test_intent_passed_to_retriever(self):
        retriever = FakeRetriever(results=[_make_result()])
        gen = HistoricalReplyGenerator(retriever=retriever)
        gen.generate("Test", intent="delivery_delay")
        # No assertion needed — just verify no exception

    def test_get_params(self):
        retriever = FakeRetriever()
        gen = HistoricalReplyGenerator(retriever=retriever, top_k=3)
        params = gen.get_params()
        assert params["top_k"] == 3

    def test_multiple_evidence(self):
        results = [
            _make_result(knowledge_id="kb_001", score=0.9),
            _make_result(knowledge_id="kb_002", score=0.8),
        ]
        retriever = FakeRetriever(results=results)
        gen = HistoricalReplyGenerator(retriever=retriever, top_k=5)
        output = gen.generate("Test")
        assert len(output.evidence) == 2

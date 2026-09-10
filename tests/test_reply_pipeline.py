"""Tests for reply pipeline."""

import pytest
from src.generation.reply_pipeline import ReplyPipeline
from src.generation.generic_baseline import GenericReplyGenerator
from src.generation.historical_baseline import HistoricalReplyGenerator
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


def _make_result(knowledge_id="kb_001", support_response="DM us.", score=0.9, customer_message="Help me"):
    return RetrievalResult(
        rank=1,
        knowledge_id=knowledge_id,
        customer_message=customer_message,
        support_response=support_response,
        similarity_score=score,
    )


class TestReplyPipeline:
    def test_historical_with_evidence(self):
        retriever = FakeRetriever(results=[_make_result()])
        pipeline = ReplyPipeline(retriever=retriever, generic_fallback=False, detect_safety=False)
        result = pipeline.generate("My order is late")
        assert result.reply == "DM us."
        assert result.generation_method == "historical_baseline"

    def test_fallback_to_generic(self):
        retriever = FakeRetriever(results=[], status="insufficient_evidence")
        pipeline = ReplyPipeline(retriever=retriever, generic_fallback=True, detect_safety=False)
        result = pipeline.generate("Unknown query")
        assert result.reply is not None
        assert result.generation_method == "generic_baseline"
        assert result.metadata.get("fallback_from") == "historical_baseline"

    def test_no_fallback_when_disabled(self):
        retriever = FakeRetriever(results=[], status="insufficient_evidence")
        pipeline = ReplyPipeline(retriever=retriever, generic_fallback=False, detect_safety=False)
        result = pipeline.generate("Unknown query")
        assert result.reply is None
        assert result.status == "insufficient_evidence"

    def test_safety_detection(self):
        risky = RetrievalResult(
            rank=1,
            knowledge_id="kb_001",
            customer_message="Help me",
            support_response="Email us at support@example.com",
            similarity_score=0.9,
        )
        retriever = FakeRetriever(results=[risky])
        pipeline = ReplyPipeline(retriever=retriever, generic_fallback=False, detect_safety=True)
        result = pipeline.generate("Help me")
        assert "contains_email" in result.risk_flags

    def test_schema_valid(self):
        retriever = FakeRetriever(results=[_make_result()])
        pipeline = ReplyPipeline(retriever=retriever, detect_safety=False)
        result = pipeline.generate("Test")
        assert hasattr(result, "query")
        assert hasattr(result, "reply")
        assert hasattr(result, "generation_method")
        assert hasattr(result, "status")
        assert hasattr(result, "evidence")

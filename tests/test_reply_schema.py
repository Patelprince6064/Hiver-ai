"""Tests for reply schema."""

import pytest
from src.generation.reply_schema import ReplyOutput, ReplyEvidence, build_reply_output


class TestReplyEvidence:
    def test_valid_evidence(self):
        e = ReplyEvidence(
            knowledge_id="kb_test_001",
            similarity_score=0.89,
            support_response="Please DM us your order number.",
        )
        assert e.knowledge_id == "kb_test_001"
        assert e.similarity_score == 0.89

    def test_optional_fields(self):
        e = ReplyEvidence(
            knowledge_id="kb_test_001",
            similarity_score=0.89,
            support_response="Hello",
        )
        assert e.conversation_id is None
        assert e.intent is None


class TestReplyOutput:
    def test_valid_output(self):
        out = ReplyOutput(
            query="My order is late",
            reply="Please DM us your order number.",
            generation_method="historical_baseline",
            status="success",
        )
        assert out.query == "My order is late"
        assert out.status == "success"

    def test_null_reply(self):
        out = ReplyOutput(
            query="My order is late",
            reply=None,
            generation_method="historical_baseline",
            status="insufficient_evidence",
        )
        assert out.reply is None
        assert out.status == "insufficient_evidence"


class TestBuildReplyOutput:
    def test_with_evidence(self):
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "Hello"}
        ]
        out = build_reply_output(
            query="Hi there",
            reply="Hello!",
            generation_method="historical_baseline",
            status="success",
            evidence=evidence,
            risk_flags=["contains_url"],
        )
        assert len(out.evidence) == 1
        assert out.evidence[0].knowledge_id == "kb_001"
        assert out.risk_flags == ["contains_url"]

    def test_empty_evidence(self):
        out = build_reply_output(
            query="Hi",
            reply="Hello",
            generation_method="generic_baseline",
            status="success",
        )
        assert out.evidence == []
        assert out.risk_flags == []

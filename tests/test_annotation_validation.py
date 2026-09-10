"""Tests for annotation validation."""

import pytest
from src.evaluation.reply_evaluation_schema import (
    ReplyQualityScores,
    ReplyEvaluation,
    build_reply_evaluation,
    FAILURE_TAGS,
)


class TestAnnotationValidation:
    def test_score_range_1_to_5(self):
        for score in range(1, 6):
            s = ReplyQualityScores(relevance=score)
            assert s.relevance == score

    def test_score_zero_invalid(self):
        with pytest.raises(Exception):
            ReplyQualityScores(relevance=0)

    def test_score_six_invalid(self):
        with pytest.raises(Exception):
            ReplyQualityScores(relevance=6)

    def test_all_dimensions_scored(self):
        s = ReplyQualityScores(relevance=4, groundedness=5, correctness=3, helpfulness=4, completeness=5, style=4)
        overall = s.compute_overall()
        assert overall is not None

    def test_partial_dimensions(self):
        s = ReplyQualityScores(relevance=4, correctness=5)
        overall = s.compute_overall()
        assert overall is not None
        assert abs(overall - 4.5) < 0.01

    def test_failure_tags_valid(self):
        for tag in ["unsupported_claim", "wrong_intent", "too_generic", "insufficient_evidence"]:
            assert tag in FAILURE_TAGS

    def test_failure_tags_count(self):
        assert len(FAILURE_TAGS) == 17

    def test_evaluation_with_all_fields(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test message",
            system="System A",
            system_name="grounded_llm",
            reply="Please DM us.",
            intent="shipping",
            split="dev",
            retrieval_status="success",
            evidence_ids=["KB-001"],
            grounding_status="pass",
            grounding_score=0.9,
            scores={"relevance": 5, "groundedness": 4, "correctness": 5, "helpfulness": 4, "completeness": 4, "style": 5},
            failure_tags=["unsupported_claim"],
            free_text_reason="Test reason",
        )
        assert ev.query_id == "q_0001"
        assert ev.scores.overall is not None
        assert "unsupported_claim" in ev.failure_tags

    def test_evaluation_without_optional_fields(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test",
            system="System A",
        )
        assert ev.conversation_id == ""
        assert ev.intent == ""
        assert ev.retrieval_status == "unknown"
        assert ev.evidence_ids == []

    def test_overall_is_mean(self):
        scores = {"relevance": 4, "groundedness": 4, "correctness": 4, "helpfulness": 4, "completeness": 4, "style": 4}
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test",
            system="System A",
            scores=scores,
        )
        assert ev.scores.overall == 4.0

    def test_system_label_anonymization(self):
        ev1 = build_reply_evaluation(
            query_id="q_0001", customer_message="test", system="System A", system_name="grounded_llm",
        )
        ev2 = build_reply_evaluation(
            query_id="q_0001", customer_message="test", system="System B", system_name="generic_baseline",
        )
        assert ev1.system != ev2.system
        assert ev1.system_name != ev2.system_name

    def test_reply_none_handled(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test",
            system="System A",
            reply=None,
        )
        assert ev.reply is None

    def test_grounding_score_range(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test",
            system="System A",
            grounding_score=0.85,
        )
        assert 0.0 <= ev.grounding_score <= 1.0

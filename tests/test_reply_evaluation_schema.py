"""Tests for reply_evaluation_schema module."""

import pytest
from src.evaluation.reply_evaluation_schema import (
    ReplyQualityScores,
    ReplyEvaluation,
    BlindMapping,
    EvaluationManifest,
    PairwiseComparison,
    IntentQualitySummary,
    EvaluationSummary,
    build_reply_evaluation,
    FAILURE_TAGS,
)


class TestReplyQualityScores:
    def test_valid_scores(self):
        scores = ReplyQualityScores(relevance=5, groundedness=4, correctness=5, helpfulness=4, completeness=4, style=5)
        assert scores.relevance == 5
        assert scores.groundedness == 4

    def test_compute_overall(self):
        scores = ReplyQualityScores(relevance=4, groundedness=5, correctness=4, helpfulness=5, completeness=4, style=5)
        overall = scores.compute_overall()
        assert overall is not None
        assert abs(overall - 4.5) < 0.01

    def test_compute_overall_with_none(self):
        scores = ReplyQualityScores(relevance=4, groundedness=None, correctness=5)
        overall = scores.compute_overall()
        assert overall is not None
        assert abs(overall - 4.5) < 0.01

    def test_compute_overall_all_none(self):
        scores = ReplyQualityScores()
        assert scores.compute_overall() is None

    def test_score_range_valid(self):
        scores = ReplyQualityScores(relevance=1, groundedness=5, correctness=3, helpfulness=2, completeness=4, style=1)
        assert scores.relevance == 1
        assert scores.style == 1

    def test_score_range_invalid(self):
        with pytest.raises(Exception):
            ReplyQualityScores(relevance=6)

    def test_default_none(self):
        scores = ReplyQualityScores()
        assert scores.relevance is None
        assert scores.overall is None


class TestFailureTags:
    def test_failure_tags_exist(self):
        assert len(FAILURE_TAGS) > 0
        assert "unsupported_claim" in FAILURE_TAGS
        assert "insufficient_evidence" in FAILURE_TAGS
        assert "too_generic" in FAILURE_TAGS

    def test_failure_tags_count(self):
        assert len(FAILURE_TAGS) == 17


class TestReplyEvaluation:
    def test_valid_evaluation(self):
        ev = ReplyEvaluation(
            query_id="q_0001",
            customer_message="My order is late.",
            system="System A",
            system_name="grounded_llm",
            reply="Please DM us your order number.",
        )
        assert ev.query_id == "q_0001"
        assert ev.system == "System A"
        assert ev.split == "dev"

    def test_default_fields(self):
        ev = ReplyEvaluation(query_id="q_0001", customer_message="test", system="System A")
        assert ev.conversation_id == ""
        assert ev.evidence_ids == []
        assert ev.failure_tags == []
        assert ev.scores.relevance is None


class TestBuildReplyEvaluation:
    def test_build_with_scores(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="My order is late.",
            system="System A",
            system_name="grounded_llm",
            reply="Please DM us.",
            scores={"relevance": 5, "groundedness": 4, "correctness": 5, "helpfulness": 4, "completeness": 4, "style": 5},
        )
        assert ev.scores.relevance == 5
        assert ev.scores.overall is not None
        assert abs(ev.scores.overall - 4.5) < 0.01

    def test_build_without_scores(self):
        ev = build_reply_evaluation(
            query_id="q_0001",
            customer_message="test",
            system="System A",
        )
        assert ev.scores.relevance is None
        assert ev.scores.overall is None


class TestPairwiseComparison:
    def test_valid_comparison(self):
        pc = PairwiseComparison(
            system_a="grounded_llm",
            system_b="historical_baseline",
            n_queries=100,
            wins_a=60,
            ties=20,
            wins_b=20,
        )
        assert pc.n_queries == 100
        assert pc.wins_a == 60


class TestBlindMapping:
    def test_valid_mapping(self):
        bm = BlindMapping(
            query_id="q_0001",
            mapping={
                "System A": "grounded_llm",
                "System B": "generic_baseline",
                "System C": "historical_baseline",
                "System D": "grounded_llm_verified",
            },
        )
        assert len(bm.mapping) == 4
        assert bm.seed == 42


class TestEvaluationManifest:
    def test_valid_manifest(self):
        manifest = EvaluationManifest(
            n_queries=150,
            seed=42,
            splits={"dev": 150},
        )
        assert manifest.n_queries == 150
        assert manifest.version == "1.0"


class TestIntentQualitySummary:
    def test_valid_summary(self):
        summary = IntentQualitySummary(
            intent="shipping",
            n_examples=20,
            mean_overall=3.8,
            mean_relevance=4.0,
            mean_groundedness=3.5,
            mean_helpfulness=3.9,
            mean_correctness=4.2,
        )
        assert summary.intent == "shipping"
        assert summary.n_examples == 20

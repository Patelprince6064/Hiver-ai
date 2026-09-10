"""Tests for automated_reply_metrics module."""

import pytest
from src.evaluation.automated_reply_metrics import (
    compute_reply_metrics,
    compute_aggregate_metrics,
    AutomatedReplyMetrics,
    AggregateAutomatedMetrics,
)


class TestComputeReplyMetrics:
    def test_empty_reply(self):
        m = compute_reply_metrics(reply=None)
        assert m.is_empty is True
        assert m.is_insufficient_evidence is True

    def test_insufficient_evidence(self):
        m = compute_reply_metrics(reply="INSUFFICIENT_EVIDENCE")
        assert m.is_insufficient_evidence is True
        assert m.is_empty is False

    def test_normal_reply(self):
        m = compute_reply_metrics(reply="Please DM us your order number.")
        assert m.n_characters > 0
        assert m.n_words > 0
        assert m.n_sentences > 0
        assert m.is_empty is False

    def test_evidence_support(self):
        evidence = [{"knowledge_id": "KB-001", "support_response": "test"}]
        m = compute_reply_metrics(reply="test", evidence=evidence)
        assert m.has_evidence_support is True
        assert m.evidence_count == 1

    def test_no_evidence(self):
        m = compute_reply_metrics(reply="test", evidence=[])
        assert m.has_evidence_support is False
        assert m.evidence_count == 0

    def test_grounding_pass(self):
        m = compute_reply_metrics(reply="test", grounding_status="pass")
        assert m.grounding_pass is True

    def test_grounding_fail(self):
        m = compute_reply_metrics(reply="test", grounding_status="fail")
        assert m.grounding_pass is False

    def test_risk_flags(self):
        m = compute_reply_metrics(reply="test", risk_flags=["contains_order_id"])
        assert m.has_risk is True
        assert "contains_order_id" in m.risk_flags

    def test_no_risk(self):
        m = compute_reply_metrics(reply="test", risk_flags=[])
        assert m.has_risk is False

    def test_retrieval_status(self):
        m = compute_reply_metrics(reply="test", retrieval_status="success")
        assert m.retrieval_status == "success"

    def test_top_similarity(self):
        m = compute_reply_metrics(reply="test", top_similarity=0.85)
        assert m.top_similarity == 0.85

    def test_generation_method(self):
        m = compute_reply_metrics(reply="test", generation_method="grounded_llm")
        assert m.generation_method == "grounded_llm"

    def test_multiple_sentences(self):
        m = compute_reply_metrics(reply="First sentence. Second sentence. Third sentence.")
        assert m.n_sentences == 3

    def test_word_count(self):
        m = compute_reply_metrics(reply="one two three four five")
        assert m.n_words == 5


class TestAggregateMetrics:
    def test_empty_list(self):
        agg = compute_aggregate_metrics([])
        assert agg.n_replies == 0

    def test_single_reply(self):
        m = compute_aggregate_metrics([
            AutomatedReplyMetrics(n_characters=50, n_words=10, n_sentences=2),
        ])
        assert m.n_replies == 1
        assert m.mean_length_chars == 50.0
        assert m.mean_length_words == 10.0

    def test_multiple_replies(self):
        metrics = [
            AutomatedReplyMetrics(n_characters=100, n_words=20, grounding_pass=True),
            AutomatedReplyMetrics(n_characters=50, n_words=10, grounding_pass=False),
        ]
        agg = compute_aggregate_metrics(metrics)
        assert agg.n_replies == 2
        assert agg.mean_length_chars == 75.0
        assert agg.mean_length_words == 15.0
        assert agg.grounding_pass_rate == 0.5

    def test_empty_rate(self):
        metrics = [
            AutomatedReplyMetrics(is_empty=True),
            AutomatedReplyMetrics(is_empty=False),
            AutomatedReplyMetrics(is_empty=False),
        ]
        agg = compute_aggregate_metrics(metrics)
        assert abs(agg.empty_rate - 1 / 3) < 0.01

    def test_risk_rate(self):
        metrics = [
            AutomatedReplyMetrics(has_risk=True),
            AutomatedReplyMetrics(has_risk=False),
        ]
        agg = compute_aggregate_metrics(metrics)
        assert agg.risk_rate == 0.5

    def test_generation_method_distribution(self):
        metrics = [
            AutomatedReplyMetrics(generation_method="generic_baseline"),
            AutomatedReplyMetrics(generation_method="grounded_llm"),
            AutomatedReplyMetrics(generation_method="generic_baseline"),
        ]
        agg = compute_aggregate_metrics(metrics)
        assert agg.generation_method_distribution["generic_baseline"] == 2
        assert agg.generation_method_distribution["grounded_llm"] == 1

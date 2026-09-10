"""Tests for reply evaluation metrics."""

import pytest
from src.evaluation.reply_metrics import (
    response_coverage,
    evidence_availability,
    similarity_distribution,
    intent_consistency,
    resolution_consistency,
    safety_risk_rate,
    reply_length_distribution,
    evaluate_reply_baselines,
)


class TestResponseCoverage:
    def test_all_have_reply(self):
        preds = [{"reply": "A"}, {"reply": "B"}]
        assert response_coverage(preds) == 1.0

    def test_none_have_reply(self):
        preds = [{"reply": None}, {"reply": None}]
        assert response_coverage(preds) == 0.0

    def test_empty(self):
        assert response_coverage([]) == 0.0


class TestEvidenceAvailability:
    def test_all_have_evidence(self):
        preds = [{"evidence": [{"k": 1}]}, {"evidence": [{"k": 2}]}]
        assert evidence_availability(preds) == 1.0

    def test_some_have_evidence(self):
        preds = [{"evidence": [{"k": 1}]}, {"evidence": []}]
        assert evidence_availability(preds) == 0.5


class TestSimilarityDistribution:
    def test_with_scores(self):
        preds = [
            {"evidence": [{"similarity_score": 0.9}]},
            {"evidence": [{"similarity_score": 0.7}]},
        ]
        dist = similarity_distribution(preds)
        assert dist["mean"] == pytest.approx(0.8)
        assert dist["min"] == 0.7
        assert dist["max"] == 0.9

    def test_empty(self):
        dist = similarity_distribution([])
        assert dist["mean"] == 0.0


class TestIntentConsistency:
    def test_all_match(self):
        preds = [
            {"predicted_intent": "delivery_delay", "evidence": [{"intent": "delivery_delay"}]},
        ]
        assert intent_consistency(preds) == 1.0

    def test_none_match(self):
        preds = [
            {"predicted_intent": "refund", "evidence": [{"intent": "delivery_delay"}]},
        ]
        assert intent_consistency(preds) == 0.0

    def test_no_evidence(self):
        preds = [{"predicted_intent": "refund", "evidence": []}]
        assert intent_consistency(preds) == 0.0


class TestResolutionConsistency:
    def test_compatible(self):
        preds = [
            {
                "predicted_intent": "delivery_delay",
                "evidence": [{"resolution_type": "delivery_delay"}],
            },
        ]
        assert resolution_consistency(preds) == 1.0

    def test_incompatible(self):
        preds = [
            {
                "predicted_intent": "billing",
                "evidence": [{"resolution_type": "delivery_delay"}],
            },
        ]
        assert resolution_consistency(preds) == 0.0


class TestSafetyRiskRate:
    def test_all_risky(self):
        preds = [{"risk_flags": ["contains_email"]}, {"risk_flags": ["contains_url"]}]
        assert safety_risk_rate(preds) == 1.0

    def test_none_risky(self):
        preds = [{"risk_flags": []}, {"risk_flags": []}]
        assert safety_risk_rate(preds) == 0.0


class TestReplyLengthDistribution:
    def test_with_replies(self):
        preds = [{"reply": "Hello world"}, {"reply": "Hi"}]
        dist = reply_length_distribution(preds)
        assert dist["min"] == 1
        assert dist["max"] == 2

    def test_empty(self):
        dist = reply_length_distribution([])
        assert dist["mean"] == 0


class TestEvaluateReplyBaselines:
    def test_returns_both_metrics(self):
        generic = [{"reply": "Generic", "evidence": [], "risk_flags": []}]
        historical = [{"reply": "Historical", "evidence": [{"similarity_score": 0.9}], "risk_flags": []}]
        result = evaluate_reply_baselines(generic, historical)
        assert "generic_baseline" in result
        assert "historical_baseline" in result
        assert result["generic_baseline"]["n_queries"] == 1
        assert result["historical_baseline"]["n_queries"] == 1

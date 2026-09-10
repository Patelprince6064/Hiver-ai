"""Tests for escalation_metrics.py."""

import pytest
from src.evaluation.escalation_metrics import (
    EscalationMetrics,
    compute_escalation_metrics,
    compute_threshold_analysis,
)


class TestEscalationMetrics:
    def test_perfect_predictions(self):
        predictions = ["AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        gold = ["AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        m = compute_escalation_metrics(predictions, gold)
        assert m.accuracy == 1.0
        assert m.false_auto_handle_rate == 0.0
        assert m.auto_f1 == 1.0
        assert m.escalate_f1 == 1.0

    def test_all_wrong(self):
        predictions = ["AUTO_HANDLE", "AUTO_HANDLE"]
        gold = ["ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        m = compute_escalation_metrics(predictions, gold)
        assert m.accuracy == 0.0
        assert m.false_auto_handle_rate == 1.0

    def test_mixed_predictions(self):
        predictions = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "AUTO_HANDLE"]
        gold = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        m = compute_escalation_metrics(predictions, gold)
        assert m.accuracy == pytest.approx(2 / 3)
        assert m.false_auto_handle_rate == 0.5

    def test_empty_predictions(self):
        m = compute_escalation_metrics([], [])
        assert m.n_total == 0
        assert m.accuracy == 0.0

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            compute_escalation_metrics(["AUTO_HANDLE"], ["AUTO_HANDLE", "ESCALATE_TO_HUMAN"])

    def test_false_auto_handle_rate_key_metric(self):
        predictions = ["AUTO_HANDLE"] * 10
        gold = ["ESCALATE_TO_HUMAN"] * 3 + ["AUTO_HANDLE"] * 7
        m = compute_escalation_metrics(predictions, gold)
        assert m.false_auto_handle_rate == pytest.approx(3 / 3)

    def test_safe_auto_handle_rate(self):
        predictions = ["AUTO_HANDLE"] * 8 + ["ESCALATE_TO_HUMAN"] * 2
        gold = ["AUTO_HANDLE"] * 6 + ["ESCALATE_TO_HUMAN"] * 4
        m = compute_escalation_metrics(predictions, gold)
        assert m.safe_auto_handle_rate == pytest.approx(6 / 8)

    def test_auto_handle_rate(self):
        predictions = ["AUTO_HANDLE"] * 3 + ["ESCALATE_TO_HUMAN"] * 7
        gold = predictions[:]
        m = compute_escalation_metrics(predictions, gold)
        assert m.auto_handle_rate == pytest.approx(0.3)
        assert m.escalate_rate == pytest.approx(0.7)

    def test_precision_recall_f1(self):
        predictions = ["AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN"]
        gold = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        m = compute_escalation_metrics(predictions, gold)
        assert m.auto_precision == pytest.approx(0.5)
        assert m.auto_recall == pytest.approx(1.0)
        assert m.escalate_precision == pytest.approx(1.0)
        assert m.escalate_recall == pytest.approx(0.5)

    def test_escalate_rate(self):
        predictions = ["ESCALATE_TO_HUMAN"] * 7 + ["AUTO_HANDLE"] * 3
        gold = predictions[:]
        m = compute_escalation_metrics(predictions, gold)
        assert m.escalate_rate == pytest.approx(0.7)


class TestThresholdAnalysis:
    def test_basic_thresholds(self):
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
        gold = ["AUTO_HANDLE"] * 4 + ["ESCALATE_TO_HUMAN"] * 4
        results = compute_threshold_analysis(scores, gold, thresholds=[0.5, 0.7])
        assert len(results) == 2
        assert results[0]["threshold"] == 0.5
        assert results[1]["threshold"] == 0.7
        for r in results:
            assert 0.0 <= r["auto_handle_rate"] <= 1.0
            assert 0.0 <= r["false_auto_handle_rate"] <= 1.0

    def test_empty_scores(self):
        results = compute_threshold_analysis([], [])
        assert results == []

    def test_default_thresholds(self):
        scores = [0.5] * 10
        gold = ["AUTO_HANDLE"] * 10
        results = compute_threshold_analysis(scores, gold)
        assert len(results) == 10

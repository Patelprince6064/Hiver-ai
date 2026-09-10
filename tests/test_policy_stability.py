"""Tests for policy stability analysis."""

import pytest
from src.evaluation.escalation_metrics import compute_escalation_metrics, compute_threshold_analysis


class TestPolicyStability:
    def test_threshold_analysis_deterministic(self):
        confidence_scores = [0.5, 0.6, 0.7, 0.8, 0.9]
        gold_labels = [
            "AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN",
            "AUTO_HANDLE", "ESCALATE_TO_HUMAN",
        ]

        results1 = compute_threshold_analysis(confidence_scores, gold_labels, [0.5, 0.7, 0.9])
        results2 = compute_threshold_analysis(confidence_scores, gold_labels, [0.5, 0.7, 0.9])

        assert results1 == results2

    def test_higher_threshold_fewer_auto_handles(self):
        confidence_scores = [0.5, 0.6, 0.7, 0.8, 0.9]
        gold_labels = ["AUTO_HANDLE"] * 5

        low_thresh = compute_threshold_analysis(confidence_scores, gold_labels, [0.5])
        high_thresh = compute_threshold_analysis(confidence_scores, gold_labels, [0.9])

        assert low_thresh[0]["n_auto_handle"] >= high_thresh[0]["n_auto_handle"]

    def test_metrics_deterministic(self):
        predictions = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "AUTO_HANDLE"]
        gold = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]

        m1 = compute_escalation_metrics(predictions, gold)
        m2 = compute_escalation_metrics(predictions, gold)

        assert m1.accuracy == m2.accuracy
        assert m1.false_auto_handle_rate == m2.false_auto_handle_rate

    def test_empty_data(self):
        results = compute_threshold_analysis([], [], [0.5])
        assert results == []

    def test_threshold_boundary(self):
        confidence_scores = [0.7, 0.7, 0.7]
        gold_labels = ["AUTO_HANDLE", "ESCALATE_TO_HUMAN", "AUTO_HANDLE"]

        results = compute_threshold_analysis(confidence_scores, gold_labels, [0.7])
        # At threshold 0.7, all scores >= 0.7 → AUTO_HANDLE
        assert results[0]["n_auto_handle"] == 3

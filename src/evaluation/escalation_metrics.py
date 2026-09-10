"""Escalation evaluation metrics.

Calculates escalation-specific metrics when gold labels are available.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EscalationMetrics:
    """Aggregated escalation metrics."""

    n_total: int = 0
    n_auto_handle: int = 0
    n_escalate: int = 0

    n_true_auto: int = 0
    n_true_escalate: int = 0
    n_pred_auto: int = 0
    n_pred_escalate: int = 0

    tp_auto: int = 0
    fp_auto: int = 0
    fn_auto: int = 0
    tn_auto: int = 0

    tp_escalate: int = 0
    fp_escalate: int = 0
    fn_escalate: int = 0
    tn_escalate: int = 0

    accuracy: float = 0.0
    auto_handle_rate: float = 0.0
    escalate_rate: float = 0.0

    auto_precision: float = 0.0
    auto_recall: float = 0.0
    auto_f1: float = 0.0

    escalate_precision: float = 0.0
    escalate_recall: float = 0.0
    escalate_f1: float = 0.0

    false_auto_handle_rate: float = 0.0
    false_escalation_rate: float = 0.0

    safe_auto_handle_rate: float = 0.0

    details: dict[str, Any] = field(default_factory=dict)


def compute_escalation_metrics(
    predictions: list[str],
    gold_labels: list[str],
) -> EscalationMetrics:
    """Compute escalation metrics from predictions and gold labels.

    Args:
        predictions: List of "AUTO_HANDLE" or "ESCALATE_TO_HUMAN".
        gold_labels: List of "AUTO_HANDLE" or "ESCALATE_TO_HUMAN".

    Returns:
        EscalationMetrics with computed metrics.
    """
    if len(predictions) != len(gold_labels):
        raise ValueError("predictions and gold_labels must have the same length")

    n = len(predictions)
    if n == 0:
        return EscalationMetrics()

    metrics = EscalationMetrics(n_total=n)

    metrics.n_pred_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
    metrics.n_pred_escalate = sum(1 for p in predictions if p == "ESCALATE_TO_HUMAN")
    metrics.n_true_auto = sum(1 for g in gold_labels if g == "AUTO_HANDLE")
    metrics.n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")

    metrics.n_auto_handle = metrics.n_pred_auto
    metrics.n_escalate = metrics.n_pred_escalate

    for pred, gold in zip(predictions, gold_labels):
        if pred == "AUTO_HANDLE" and gold == "AUTO_HANDLE":
            metrics.tp_auto += 1
            metrics.tn_escalate += 1
        elif pred == "AUTO_HANDLE" and gold == "ESCALATE_TO_HUMAN":
            metrics.fp_auto += 1
            metrics.fn_escalate += 1
        elif pred == "ESCALATE_TO_HUMAN" and gold == "ESCALATE_TO_HUMAN":
            metrics.tp_escalate += 1
            metrics.tn_auto += 1
        elif pred == "ESCALATE_TO_HUMAN" and gold == "AUTO_HANDLE":
            metrics.fp_escalate += 1
            metrics.fn_auto += 1

    correct = metrics.tp_auto + metrics.tp_escalate
    metrics.accuracy = correct / n if n else 0.0

    metrics.auto_handle_rate = metrics.n_pred_auto / n if n else 0.0
    metrics.escalate_rate = metrics.n_pred_escalate / n if n else 0.0

    metrics.auto_precision = metrics.tp_auto / (metrics.tp_auto + metrics.fp_auto) if (metrics.tp_auto + metrics.fp_auto) > 0 else 0.0
    metrics.auto_recall = metrics.tp_auto / (metrics.tp_auto + metrics.fn_auto) if (metrics.tp_auto + metrics.fn_auto) > 0 else 0.0
    metrics.auto_f1 = (
        2 * metrics.auto_precision * metrics.auto_recall / (metrics.auto_precision + metrics.auto_recall)
        if (metrics.auto_precision + metrics.auto_recall) > 0 else 0.0
    )

    metrics.escalate_precision = metrics.tp_escalate / (metrics.tp_escalate + metrics.fp_escalate) if (metrics.tp_escalate + metrics.fp_escalate) > 0 else 0.0
    metrics.escalate_recall = metrics.tp_escalate / (metrics.tp_escalate + metrics.fn_escalate) if (metrics.tp_escalate + metrics.fn_escalate) > 0 else 0.0
    metrics.escalate_f1 = (
        2 * metrics.escalate_precision * metrics.escalate_recall / (metrics.escalate_precision + metrics.escalate_recall)
        if (metrics.escalate_precision + metrics.escalate_recall) > 0 else 0.0
    )

    if metrics.n_true_escalate > 0:
        metrics.false_auto_handle_rate = metrics.fn_escalate / metrics.n_true_escalate
    else:
        metrics.false_auto_handle_rate = 0.0

    if metrics.n_true_auto > 0:
        metrics.false_escalation_rate = metrics.fn_auto / metrics.n_true_auto
    else:
        metrics.false_escalation_rate = 0.0

    if metrics.n_pred_auto > 0:
        metrics.safe_auto_handle_rate = metrics.tp_auto / metrics.n_pred_auto
    else:
        metrics.safe_auto_handle_rate = 0.0

    metrics.details = {
        "tp_auto": metrics.tp_auto,
        "fp_auto": metrics.fp_auto,
        "fn_auto": metrics.fn_auto,
        "tn_auto": metrics.tn_auto,
        "tp_escalate": metrics.tp_escalate,
        "fp_escalate": metrics.fp_escalate,
        "fn_escalate": metrics.fn_escalate,
        "tn_escalate": metrics.tn_escalate,
    }

    return metrics


def compute_threshold_analysis(
    confidence_scores: list[float],
    gold_labels: list[str],
    thresholds: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Analyze auto-handle rate vs false auto-handle rate at different thresholds.

    Args:
        confidence_scores: Policy confidence scores (higher = more confident auto-handle).
        gold_labels: Gold labels ("AUTO_HANDLE" or "ESCALATE_TO_HUMAN").
        thresholds: List of confidence thresholds to test.

    Returns:
        List of dicts with threshold, auto_handle_rate, false_auto_handle_rate.
    """
    if thresholds is None:
        thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    n = len(confidence_scores)
    if n == 0:
        return []

    results = []
    for threshold in thresholds:
        predictions = []
        for score in confidence_scores:
            if score >= threshold:
                predictions.append("AUTO_HANDLE")
            else:
                predictions.append("ESCALATE_TO_HUMAN")

        n_pred_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
        n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")

        fn_escalate = 0
        for pred, gold in zip(predictions, gold_labels):
            if pred == "AUTO_HANDLE" and gold == "ESCALATE_TO_HUMAN":
                fn_escalate += 1

        auto_handle_rate = n_pred_auto / n if n else 0.0
        false_auto_handle_rate = fn_escalate / n_true_escalate if n_true_escalate > 0 else 0.0

        results.append({
            "threshold": threshold,
            "auto_handle_rate": round(auto_handle_rate, 4),
            "false_auto_handle_rate": round(false_auto_handle_rate, 4),
            "n_auto_handle": n_pred_auto,
            "n_false_auto": fn_escalate,
        })

    return results

"""Evaluation result schema.

Defines structured format for evaluation results.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Structured evaluation result."""

    model: str = Field(..., description="Model identifier")
    dataset: str = Field(..., description="Dataset split name (dev/golden)")
    metrics: dict[str, float] = Field(default_factory=dict, description="Aggregate metrics")
    per_intent: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-intent metrics"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp",
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Model configuration")
    n_examples: int = Field(0, description="Number of evaluation examples")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")


def build_result(
    model: str,
    dataset: str,
    y_true: list[str],
    y_pred: list[str],
    proba: list[dict[str, float]] | None = None,
    config: dict | None = None,
) -> EvaluationResult:
    """Build an EvaluationResult from true/predicted labels."""
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        f1_score,
        precision_score,
        recall_score,
    )

    accuracy = accuracy_score(y_true, y_pred)
    macro_precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    per_intent = {}
    for label in sorted(set(y_true)):
        if label in report:
            per_intent[label] = {
                "precision": report[label]["precision"],
                "recall": report[label]["recall"],
                "f1-score": report[label]["f1-score"],
                "support": report[label]["support"],
            }

    return EvaluationResult(
        model=model,
        dataset=dataset,
        metrics={
            "accuracy": accuracy,
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
        },
        per_intent=per_intent,
        config=config or {},
        n_examples=len(y_true),
    )

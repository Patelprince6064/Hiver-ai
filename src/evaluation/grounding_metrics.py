"""Grounding metrics for evaluation.

Calculates grounding-specific metrics across a set of predictions.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundingMetrics:
    """Aggregated grounding metrics."""

    n_replies: int = 0
    grounding_pass_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    high_risk_unsupported_rate: float = 0.0
    historical_identifier_leak_rate: float = 0.0
    repair_rate: float = 0.0
    repair_success_rate: float = 0.0
    final_rejection_rate: float = 0.0
    insufficient_evidence_rate: float = 0.0
    avg_grounding_score: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


def compute_grounding_metrics(
    verifications: list[dict[str, Any]],
) -> GroundingMetrics:
    """Compute grounding metrics from verification results.

    Args:
        verifications: List of verification result dicts.

    Returns:
        GroundingMetrics with computed metrics.
    """
    if not verifications:
        return GroundingMetrics()

    n = len(verifications)

    n_pass = sum(1 for v in verifications if v.get("status") == "pass")
    n_fail = sum(1 for v in verifications if v.get("status") == "fail")
    n_review = sum(1 for v in verifications if v.get("status") == "review")
    n_insufficient = sum(1 for v in verifications if v.get("status") == "insufficient_evidence")

    n_unsupported = sum(1 for v in verifications if v.get("unsupported_claims"))
    n_high_risk = sum(
        1 for v in verifications
        if any("unsupported_high_risk" in f for f in v.get("risk_flags", []))
    )
    n_id_leak = sum(
        1 for v in verifications
        if any("contains_order_id" in f or "historical_pii" in f for f in v.get("risk_flags", []))
    )

    n_repaired = sum(1 for v in verifications if v.get("repair_attempted"))
    n_repair_success = sum(
        1 for v in verifications
        if v.get("repair_attempted") and v.get("repair_succeeded")
    )

    n_final_reject = sum(
        1 for v in verifications
        if v.get("final_status") in ("fail", "insufficient_evidence")
    )

    scores = [v.get("grounding_score", 0.0) for v in verifications]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    return GroundingMetrics(
        n_replies=n,
        grounding_pass_rate=n_pass / n if n else 0.0,
        unsupported_claim_rate=n_unsupported / n if n else 0.0,
        high_risk_unsupported_rate=n_high_risk / n if n else 0.0,
        historical_identifier_leak_rate=n_id_leak / n if n else 0.0,
        repair_rate=n_repaired / n if n else 0.0,
        repair_success_rate=n_repair_success / n_repaired if n_repaired else 0.0,
        final_rejection_rate=n_final_reject / n if n else 0.0,
        insufficient_evidence_rate=n_insufficient / n if n else 0.0,
        avg_grounding_score=avg_score,
        details={
            "n_pass": n_pass,
            "n_fail": n_fail,
            "n_review": n_review,
            "n_insufficient": n_insufficient,
            "n_unsupported": n_unsupported,
            "n_high_risk": n_high_risk,
            "n_id_leak": n_id_leak,
            "n_repaired": n_repaired,
            "n_repair_success": n_repair_success,
            "n_final_reject": n_final_reject,
        },
    )

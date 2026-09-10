"""Hybrid grounding score computation.

Combines deterministic and semantic checks into a single grounding verdict.
"""

from dataclasses import dataclass, field
from typing import Any

from src.evaluation.claim_extractor import Claim
from src.evaluation.evidence_support import SupportResult
from src.evaluation.fact_types import HIGH_RISK_TYPE_NAMES, FactType


@dataclass
class GroundingVerdict:
    """Final grounding verdict for a reply."""

    status: str  # pass | review | fail | insufficient_evidence
    grounding_score: float = 0.0
    claims: list[dict[str, Any]] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    evidence_used: list[str] = field(default_factory=list)
    reason: str = ""


def compute_grounding_verdict(
    reply_text: str,
    claims: list[Claim],
    support_results: list[SupportResult],
    numeric_result: Any = None,
    url_result: Any = None,
    pii_result: Any = None,
    semantic_result: Any = None,
    evidence: list[dict[str, Any]] | None = None,
) -> GroundingVerdict:
    """Compute the final grounding verdict.

    Policy (in order of priority):
    1. If no evidence and reply exists -> insufficient_evidence
    2. If unsupported high-risk claim -> fail
    3. If historical identifier leaked -> fail
    4. If unsupported URL -> fail
    5. If multiple unsupported claims -> fail
    6. If any unsupported claim -> review
    7. If semantic score low -> review
    8. Otherwise -> pass

    Args:
        reply_text: The generated reply.
        claims: Extracted claims.
        support_results: Support check results for each claim.
        numeric_result: NumericCheckResult (optional).
        url_result: URLCheckResult (optional).
        pii_result: SafetyResult (optional).
        semantic_result: SemanticGroundingResult (optional).
        evidence: The evidence used.

    Returns:
        GroundingVerdict with status and details.
    """
    if not reply_text:
        return GroundingVerdict(
            status="insufficient_evidence",
            reason="No reply generated.",
        )

    risk_flags: list[str] = []
    unsupported_claims: list[dict[str, Any]] = []
    evidence_ids: list[str] = []

    if evidence:
        evidence_ids = [e.get("knowledge_id", "") for e in evidence]

    if not evidence:
        return GroundingVerdict(
            status="insufficient_evidence",
            grounding_score=0.0,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)] if claims else [],
            risk_flags=[],
            unsupported_claims=[],
            evidence_used=[],
            reason="No evidence available for grounding check.",
        )

    for claim, support in zip(claims, support_results):
        claim_dict = _claim_to_dict(claim, support)
        if not support.supported:
            unsupported_claims.append(claim_dict)
            if claim.fact_type.value in HIGH_RISK_TYPE_NAMES:
                risk_flags.append(f"unsupported_high_risk_{claim.fact_type.value}")

    if numeric_result and not numeric_result.passed:
        for uc in numeric_result.unsupported:
            risk_flags.append(f"unsupported_numeric_{uc.category}")
            unsupported_claims.append({
                "claim": uc.text,
                "type": "numeric",
                "supported": False,
                "evidence_ids": [],
            })

    if url_result and not url_result.passed:
        for uu in url_result.unsupported:
            risk_flags.append("unsupported_url")
            unsupported_claims.append({
                "claim": uu.url,
                "type": "url",
                "supported": False,
                "evidence_ids": [],
            })

    if pii_result and pii_result.has_risk:
        for flag in pii_result.flags:
            risk_flags.append(flag)

    if semantic_result and not semantic_result.passed:
        risk_flags.append("low_semantic_grounding")

    if any("unsupported_high_risk" in f for f in risk_flags):
        return GroundingVerdict(
            status="fail",
            grounding_score=0.0,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason="Unsupported high-risk claims detected.",
        )

    if any("unsupported_url" in f for f in risk_flags):
        return GroundingVerdict(
            status="fail",
            grounding_score=0.1,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason="Unsupported URL detected.",
        )

    if any("contains_order_id" in f or "historical_pii" in f for f in risk_flags):
        return GroundingVerdict(
            status="fail",
            grounding_score=0.1,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason="Historical identifier/PII leakage detected.",
        )

    if len(unsupported_claims) > 1:
        return GroundingVerdict(
            status="fail",
            grounding_score=0.2,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason=f"Multiple unsupported claims ({len(unsupported_claims)}).",
        )

    if len(unsupported_claims) == 1:
        return GroundingVerdict(
            status="review",
            grounding_score=0.5,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason="One unsupported claim detected. Needs review.",
        )

    if semantic_result and not semantic_result.passed:
        return GroundingVerdict(
            status="review",
            grounding_score=0.4,
            claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
            risk_flags=risk_flags,
            unsupported_claims=unsupported_claims,
            evidence_used=evidence_ids,
            reason="Low semantic grounding score.",
        )

    supported_count = sum(1 for s in support_results if s.supported)
    total = len(support_results) if support_results else 1
    score = supported_count / total

    return GroundingVerdict(
        status="pass",
        grounding_score=score,
        claims=[_claim_to_dict(c, s) for c, s in zip(claims, support_results)],
        risk_flags=risk_flags,
        unsupported_claims=unsupported_claims,
        evidence_used=evidence_ids,
        reason="All detected claims are supported by supplied evidence.",
    )


def _claim_to_dict(claim: Claim, support: SupportResult) -> dict[str, Any]:
    """Convert claim and support result to dict."""
    return {
        "claim": claim.text,
        "type": claim.fact_type.value,
        "supported": support.supported,
        "confidence": support.confidence,
        "support_source": support.support_source,
        "evidence_ids": support.supporting_evidence_ids,
        "reason": support.reason,
    }

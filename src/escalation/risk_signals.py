"""Risk signal extraction.

Deterministic functions that extract risk signals from pipeline outputs.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskSignals:
    """Container for all extracted risk signals."""

    intent_confidence: float | None = None
    intent_top2_confidence: float | None = None
    confidence_margin: float | None = None
    retrieval_available: bool = False
    retrieval_status: str = "unknown"
    top_similarity: float | None = None
    evidence_count: int = 0
    retrieval_quality_score: float | None = None
    grounding_status: str = "unknown"
    grounding_score: float | None = None
    has_high_risk_claims: bool = False
    high_risk_claim_types: list[str] = field(default_factory=list)
    has_unsupported_claims: bool = False
    unsupported_claim_count: int = 0
    reply_valid: bool = True
    reply_status: str = "success"
    has_safety_risk: bool = False
    safety_risk_flags: list[str] = field(default_factory=list)
    is_provider_error: bool = False
    is_multi_intent: bool = False
    is_ambiguous: bool = False
    requires_account_action: bool = False
    requires_order_action: bool = False
    requires_personal_info: bool = False
    has_financial_claim: bool = False
    grounding_repair_attempted: bool = False
    grounding_repair_succeeded: bool = False
    is_high_risk_request: bool = False
    high_risk_request_categories: list[str] = field(default_factory=list)
    conversation_complexity_score: float | None = None
    conversation_complexity_level: str = "low"
    has_repeated_unresolved_issue: bool = False


def extract_signals(
    intent_result: dict[str, Any] | None = None,
    retrieval_result: dict[str, Any] | None = None,
    reply_result: dict[str, Any] | None = None,
    grounding_result: dict[str, Any] | None = None,
) -> RiskSignals:
    """Extract risk signals from pipeline outputs.

    Args:
        intent_result: Dict with 'intent', 'confidence', 'probabilities'.
        retrieval_result: Dict with 'status', 'results', 'top_similarity'.
        reply_result: Dict with 'status', 'reply', 'risk_flags', 'generation_method'.
        grounding_result: Dict with 'status', 'grounding_score', 'risk_flags',
                          'unsupported_claims', 'repair_attempted', 'repair_succeeded'.

    Returns:
        RiskSignals with all extracted signals.
    """
    signals = RiskSignals()

    if intent_result:
        signals.intent_confidence = intent_result.get("confidence")
        intent = intent_result.get("intent", "")
        probabilities = intent_result.get("probabilities", {})

        if probabilities:
            sorted_probs = sorted(probabilities.values(), reverse=True)
            if len(sorted_probs) >= 2:
                signals.intent_top2_confidence = sorted_probs[1]
                signals.confidence_margin = sorted_probs[0] - sorted_probs[1]
                if signals.confidence_margin < 0.15 and sorted_probs[1] > 0.25:
                    signals.is_multi_intent = True
                if sorted_probs[0] < 0.4:
                    signals.is_ambiguous = True

    if retrieval_result:
        status = retrieval_result.get("retrieval_status", retrieval_result.get("status", "unknown"))
        signals.retrieval_status = status
        results = retrieval_result.get("results", [])
        signals.evidence_count = len(results)
        signals.retrieval_available = len(results) > 0 and status == "success"

        if results:
            signals.top_similarity = results[0].get("similarity_score")

        # Compute retrieval quality score (0.0 to 1.0)
        quality_score = 0.0
        if signals.retrieval_available:
            # Base score for having evidence
            quality_score += 0.3

            # Top similarity contribution
            if signals.top_similarity is not None:
                quality_score += min(signals.top_similarity * 0.4, 0.4)

            # Evidence count contribution
            quality_score += min(signals.evidence_count / 5.0, 0.3)

        signals.retrieval_quality_score = min(quality_score, 1.0)

    if reply_result:
        reply_status = reply_result.get("status", "success")
        reply_text = reply_result.get("reply")
        signals.reply_status = reply_status
        signals.reply_valid = reply_status == "success" and reply_text is not None and len(reply_text.strip()) > 0
        signals.is_provider_error = reply_status == "provider_error"
        signals.safety_risk_flags = reply_result.get("risk_flags", [])
        signals.has_safety_risk = bool(signals.safety_risk_flags)

    if grounding_result:
        g_status = grounding_result.get("status", "unknown")
        signals.grounding_status = g_status
        signals.grounding_score = grounding_result.get("grounding_score")
        signals.has_unsupported_claims = bool(grounding_result.get("unsupported_claims"))
        signals.unsupported_claim_count = len(grounding_result.get("unsupported_claims", []))
        signals.grounding_repair_attempted = grounding_result.get("repair_attempted", False)
        signals.grounding_repair_succeeded = grounding_result.get("repair_succeeded", False)

        risk_flags = grounding_result.get("risk_flags", [])
        high_risk_types = {"unsupported_high_risk_price", "unsupported_high_risk_refund",
                           "unsupported_high_risk_guarantee", "unsupported_high_risk_timeline",
                           "unsupported_high_risk_account_action", "unsupported_high_risk_order_status",
                           "unsupported_high_risk_identifier", "unsupported_high_risk_personal_information",
                           "unsupported_high_risk_financial_claim"}

        for flag in risk_flags:
            if flag.startswith("unsupported_high_risk_"):
                claim_type = flag.replace("unsupported_high_risk_", "")
                signals.has_high_risk_claims = True
                signals.high_risk_claim_types.append(claim_type)

        if g_status == "fail":
            signals.has_high_risk_claims = True

    if reply_result:
        risk_flags = reply_result.get("risk_flags", [])
        for flag in risk_flags:
            if "order" in flag.lower():
                signals.requires_order_action = True
            if "account" in flag.lower():
                signals.requires_account_action = True
            if "personal" in flag.lower() or "email" in flag.lower() or "phone" in flag.lower():
                signals.requires_personal_info = True
            if "financial" in flag.lower() or "refund" in flag.lower():
                signals.has_financial_claim = True

    if grounding_result:
        for uc in grounding_result.get("unsupported_claims", []):
            claim_type = uc.get("type", "")
            if claim_type in ("price", "refund", "guarantee", "timeline", "financial_claim"):
                signals.has_financial_claim = True
            if claim_type == "identifier":
                signals.requires_order_action = True

    return signals


def signals_to_dict(signals: RiskSignals) -> dict[str, Any]:
    """Convert RiskSignals to a plain dict for serialization."""
    return {
        "intent_confidence": signals.intent_confidence,
        "intent_top2_confidence": signals.intent_top2_confidence,
        "confidence_margin": signals.confidence_margin,
        "retrieval_available": signals.retrieval_available,
        "retrieval_status": signals.retrieval_status,
        "top_similarity": signals.top_similarity,
        "evidence_count": signals.evidence_count,
        "retrieval_quality_score": signals.retrieval_quality_score,
        "grounding_status": signals.grounding_status,
        "grounding_score": signals.grounding_score,
        "has_high_risk_claims": signals.has_high_risk_claims,
        "high_risk_claim_types": signals.high_risk_claim_types,
        "has_unsupported_claims": signals.has_unsupported_claims,
        "unsupported_claim_count": signals.unsupported_claim_count,
        "reply_valid": signals.reply_valid,
        "reply_status": signals.reply_status,
        "has_safety_risk": signals.has_safety_risk,
        "safety_risk_flags": signals.safety_risk_flags,
        "is_provider_error": signals.is_provider_error,
        "is_multi_intent": signals.is_multi_intent,
        "is_ambiguous": signals.is_ambiguous,
        "requires_account_action": signals.requires_account_action,
        "requires_order_action": signals.requires_order_action,
        "requires_personal_info": signals.requires_personal_info,
        "has_financial_claim": signals.has_financial_claim,
        "grounding_repair_attempted": signals.grounding_repair_attempted,
        "grounding_repair_succeeded": signals.grounding_repair_succeeded,
        "is_high_risk_request": signals.is_high_risk_request,
        "high_risk_request_categories": signals.high_risk_request_categories,
        "conversation_complexity_score": signals.conversation_complexity_score,
        "conversation_complexity_level": signals.conversation_complexity_level,
        "has_repeated_unresolved_issue": signals.has_repeated_unresolved_issue,
    }

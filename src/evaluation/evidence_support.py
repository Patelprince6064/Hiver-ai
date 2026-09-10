"""Evidence support checking.

Determines whether extracted claims are supported by historical evidence.
"""

from dataclasses import dataclass, field
from typing import Any

from src.evaluation.claim_extractor import Claim


@dataclass
class SupportResult:
    """Result of checking claim support against evidence."""

    claim_text: str
    supported: bool
    confidence: float
    support_source: str  # "evidence" | "customer_message" | "none"
    supporting_evidence_ids: list[str] = field(default_factory=list)
    reason: str = ""


def check_claim_support(
    claim: Claim,
    evidence: list[dict[str, Any]],
    customer_message: str,
) -> SupportResult:
    """Check if a claim is supported by evidence or customer message.

    Args:
        claim: The extracted claim.
        evidence: List of evidence dicts from retrieval.
        customer_message: The original customer message.

    Returns:
        SupportResult indicating support status.
    """
    claim_lower = claim.text.lower()
    evidence_texts = []
    for ev in evidence:
        evidence_texts.append({
            "id": ev.get("knowledge_id", ""),
            "text": ev.get("support_response", "").lower(),
            "customer": ev.get("customer_message", "").lower(),
        })

    customer_lower = customer_message.lower()

    if not claim_lower.strip():
        return SupportResult(
            claim_text=claim.text,
            supported=False,
            confidence=0.0,
            support_source="none",
            supporting_evidence_ids=[],
            reason="Empty claim text.",
        )

    if _check_exact_match(claim_lower, evidence_texts):
        return SupportResult(
            claim_text=claim.text,
            supported=True,
            confidence=0.95,
            support_source="evidence",
            supporting_evidence_ids=[e["id"] for e in evidence_texts],
            reason="Claim is directly present in evidence.",
        )

    if _check_customer_match(claim_lower, customer_lower):
        return SupportResult(
            claim_text=claim.text,
            supported=True,
            confidence=0.85,
            support_source="customer_message",
            supporting_evidence_ids=[],
            reason="Claim is present in customer message.",
        )

    if _check_partial_match(claim_lower, evidence_texts):
        return SupportResult(
            claim_text=claim.text,
            supported=True,
            confidence=0.70,
            support_source="evidence",
            supporting_evidence_ids=[e["id"] for e in evidence_texts if _partial_overlap(claim_lower, e["text"])],
            reason="Claim is partially supported by evidence.",
        )

    if _check_entity_inference(claim_lower, evidence_texts):
        return SupportResult(
            claim_text=claim.text,
            supported=True,
            confidence=0.60,
            support_source="evidence",
            supporting_evidence_ids=[],
            reason="Claim can be reasonably inferred from evidence.",
        )

    return SupportResult(
        claim_text=claim.text,
        supported=False,
        confidence=0.10,
        support_source="none",
        supporting_evidence_ids=[],
        reason="No supporting evidence found for this claim.",
    )


def _check_exact_match(claim_lower: str, evidence_texts: list[dict]) -> bool:
    """Check for exact substring match in evidence."""
    for ev in evidence_texts:
        if claim_lower in ev["text"]:
            return True
    return False


def _check_customer_match(claim_lower: str, customer_lower: str) -> bool:
    """Check if claim matches customer message."""
    claim_tokens = set(claim_lower.split())
    customer_tokens = set(customer_lower.split())
    overlap = claim_tokens & customer_tokens
    return len(overlap) >= len(claim_tokens) * 0.6


def _check_partial_match(claim_lower: str, evidence_texts: list[dict]) -> bool:
    """Check for partial word overlap with evidence."""
    claim_tokens = set(claim_lower.split())
    for ev in evidence_texts:
        ev_tokens = set(ev["text"].split())
        overlap = claim_tokens & ev_tokens
        if len(overlap) >= len(claim_tokens) * 0.4 and len(overlap) >= 2:
            return True
    return False


def _check_entity_inference(claim_lower: str, evidence_texts: list[dict]) -> bool:
    """Check if claim entities are present in evidence."""
    claim_tokens = set(claim_lower.split())
    all_ev_tokens = set()
    for ev in evidence_texts:
        all_ev_tokens.update(ev["text"].split())
    overlap = claim_tokens & all_ev_tokens
    return len(overlap) >= len(claim_tokens) * 0.5 and len(overlap) >= 2


def _partial_overlap(a: str, b: str) -> float:
    """Compute token overlap between two strings."""
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0

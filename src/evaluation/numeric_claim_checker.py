"""Numeric claim checker for grounding verification.

Detects numeric claims in generated replies and checks if they are supported.
"""

import re
from dataclasses import dataclass, field
from typing import Any


PRICE_RE = re.compile(r'(?:₹|rs\.?|inr|price|cost|fee|charge|refund|amount)\s*[:\s]*\d+(?:,\d+)*(?:\.\d+)?', re.IGNORECASE)
PERCENTAGE_RE = re.compile(r'\d+(?:\.\d+)?\s*(?:%|percent)', re.IGNORECASE)
DURATION_RE = re.compile(r'\d+\s*(?:days?|hours?|minutes?|weeks?|months?|business\s*days?)', re.IGNORECASE)
QUANTITY_RE = re.compile(r'\d+\s*(?:items?|products?|orders?|packages?|units?)', re.IGNORECASE)
DATE_RE = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
ORDER_NUM_RE = re.compile(r'\b[A-Z]{2,5}[-_]?\d{4,12}\b')


@dataclass
class NumericClaim:
    """A numeric claim detected in text."""

    text: str
    category: str  # price | percentage | duration | quantity | date | order_number
    start: int
    end: int


@dataclass
class NumericCheckResult:
    """Result of numeric claim checking."""

    claims_found: list[NumericClaim] = field(default_factory=list)
    unsupported: list[NumericClaim] = field(default_factory=list)
    supported: list[NumericClaim] = field(default_factory=list)
    passed: bool = True
    issues: list[str] = field(default_factory=list)


def extract_numeric_claims(text: str) -> list[NumericClaim]:
    """Extract all numeric claims from text.

    Args:
        text: The text to analyze.

    Returns:
        List of detected NumericClaim objects.
    """
    claims: list[NumericClaim] = []

    for m in PRICE_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "price", m.start(), m.end()))

    for m in PERCENTAGE_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "percentage", m.start(), m.end()))

    for m in DURATION_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "duration", m.start(), m.end()))

    for m in QUANTITY_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "quantity", m.start(), m.end()))

    for m in DATE_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "date", m.start(), m.end()))

    for m in ORDER_NUM_RE.finditer(text):
        claims.append(NumericClaim(m.group(), "order_number", m.start(), m.end()))

    return claims


def check_numeric_claims(
    reply_text: str,
    evidence: list[dict[str, Any]],
) -> NumericCheckResult:
    """Check if numeric claims in reply are supported by evidence.

    Args:
        reply_text: The generated reply.
        evidence: List of evidence dicts from retrieval.

    Returns:
        NumericCheckResult with support status.
    """
    reply_claims = extract_numeric_claims(reply_text)

    evidence_text = " ".join(
        ev.get("support_response", "") for ev in evidence
    ) + " " + " ".join(
        ev.get("customer_message", "") for ev in evidence
    )

    evidence_claims = extract_numeric_claims(evidence_text)

    unsupported: list[NumericClaim] = []
    supported: list[NumericClaim] = []

    for rc in reply_claims:
        if _is_supported(rc, evidence_claims, evidence_text):
            supported.append(rc)
        else:
            unsupported.append(rc)

    issues = [
        f"Unsupported {uc.category}: {uc.text}" for uc in unsupported
    ]

    return NumericCheckResult(
        claims_found=reply_claims,
        unsupported=unsupported,
        supported=supported,
        passed=len(unsupported) == 0,
        issues=issues,
    )


def _is_supported(
    claim: NumericClaim,
    evidence_claims: list[NumericClaim],
    evidence_text: str,
) -> bool:
    """Check if a numeric claim is supported."""
    claim_lower = claim.text.lower()

    for ec in evidence_claims:
        if ec.text.lower() == claim_lower:
            return True

    if claim_lower in evidence_text.lower():
        return True

    claim_tokens = set(claim_lower.split())
    ev_tokens = set(evidence_text.lower().split())
    overlap = claim_tokens & ev_tokens
    if len(overlap) >= 2:
        return True

    return False

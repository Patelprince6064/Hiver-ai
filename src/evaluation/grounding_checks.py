"""Grounding checks for LLM-generated replies.

Automated checks to detect potential hallucination or grounding issues.
"""

import re
from dataclasses import dataclass, field
from typing import Any

ORDER_ID_RE = re.compile(r"\b[A-Z]{2,5}[-_]?\d{4,12}\b")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+")
NUMERIC_CLAIM_RE = re.compile(
    r"\b(?:\d+)\s*(?:days?|hours?|minutes?|%|percent|dollars?|\$)\b",
    re.IGNORECASE,
)


@dataclass
class GroundingCheckResult:
    """Result of grounding checks."""

    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def check_evidence_presence(evidence: list[dict]) -> tuple[bool, str]:
    """Check if evidence was available."""
    if not evidence:
        return False, "No evidence provided"
    return True, ""


def check_evidence_ids_valid(
    cited_ids: list[str], valid_ids: list[str]
) -> tuple[bool, str]:
    """Check if cited evidence IDs are valid."""
    valid_set = set(valid_ids)
    for eid in cited_ids:
        if eid and eid not in valid_set:
            return False, f"Invalid evidence ID: {eid}"
    return True, ""


def check_historical_pii_leakage(
    reply: str, evidence: list[dict], customer_message: str
) -> tuple[bool, str]:
    """Check if reply contains PII from historical evidence not in customer message."""
    customer_tokens = set(customer_message.lower().split())

    for ev in evidence:
        historical_response = ev.get("support_response", "")
        for pattern in [ORDER_ID_RE, EMAIL_RE, PHONE_RE, URL_RE]:
            for match in pattern.finditer(historical_response):
                matched_text = match.group()
                if matched_text in reply:
                    matched_lower = matched_text.lower()
                    if matched_lower not in customer_tokens and matched_text not in customer_message:
                        return False, f"Historical PII leaked: {matched_text}"

    return True, ""


def check_unsupported_numeric_claims(
    reply: str, evidence: list[dict]
) -> tuple[bool, str]:
    """Check for numeric claims in reply not supported by evidence."""
    reply_claims = NUMERIC_CLAIM_RE.findall(reply)
    evidence_text = " ".join(
        ev.get("support_response", "") for ev in evidence
    )
    evidence_claims = NUMERIC_CLAIM_RE.findall(evidence_text)

    for claim in reply_claims:
        claim_lower = claim.lower().strip()
        found = False
        for ev_claim in evidence_claims:
            if ev_claim.lower().strip() == claim_lower:
                found = True
                break
        if not found:
            return False, f"Unsupported numeric claim: {claim}"

    return True, ""


def check_historical_phrase_overlap(
    reply: str, evidence: list[dict], min_overlap_ratio: float = 0.1
) -> tuple[bool, str]:
    """Check that reply content comes from evidence."""
    if not evidence:
        return True, ""

    evidence_text = " ".join(
        ev.get("support_response", "") for ev in evidence
    ).lower()
    reply_words = set(reply.lower().split())
    evidence_words = set(evidence_text.split())

    if not reply_words:
        return False, "Empty reply"

    overlap = reply_words & evidence_words
    ratio = len(overlap) / len(reply_words)

    if ratio < min_overlap_ratio:
        return False, f"Low evidence overlap: {ratio:.2f}"

    return True, ""


def run_grounding_checks(
    reply: str,
    evidence: list[dict],
    customer_message: str,
    cited_evidence_ids: list[str] | None = None,
) -> GroundingCheckResult:
    """Run all grounding checks.

    Args:
        reply: The generated reply.
        evidence: The evidence used.
        customer_message: The original customer message.
        cited_evidence_ids: Evidence IDs cited in the reply.

    Returns:
        GroundingCheckResult with all check results.
    """
    all_issues = []
    checks = {}

    passed, msg = check_evidence_presence(evidence)
    checks["evidence_presence"] = passed
    if not passed:
        all_issues.append(msg)

    if cited_evidence_ids:
        valid_ids = [e.get("knowledge_id", "") for e in evidence]
        passed, msg = check_evidence_ids_valid(cited_evidence_ids, valid_ids)
        checks["evidence_ids_valid"] = passed
        if not passed:
            all_issues.append(msg)

    passed, msg = check_historical_pii_leakage(reply, evidence, customer_message)
    checks["historical_pii_leakage"] = passed
    if not passed:
        all_issues.append(msg)

    passed, msg = check_unsupported_numeric_claims(reply, evidence)
    checks["unsupported_numeric_claims"] = passed
    if not passed:
        all_issues.append(msg)

    passed, msg = check_historical_phrase_overlap(reply, evidence)
    checks["historical_phrase_overlap"] = passed
    if not passed:
        all_issues.append(msg)

    return GroundingCheckResult(
        passed=len(all_issues) == 0,
        checks=checks,
        issues=all_issues,
    )

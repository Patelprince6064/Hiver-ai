"""Resolution extraction for knowledge base construction.

Extracts resolution type and evidence from historical support responses.
"""

import re


# Resolution type patterns
RESOLUTION_PATTERNS = {
    "requested_information": [
        r"(please|kindly|could you|can you)\s+(provide|share|send|give|tell|include|specify)",
        r"(order|account|email|number|id|detail|information)\s+(number|id|detail)",
        r"dm\s+(us|me|your|the)\s+(order|account|detail)",
        r"please\s+dm\s+",
        r"send\s+(us|me)\s+(a\s+)?dm",
    ],
    "requested_private_contact": [
        r"dm\s+(us|me|your|the)",
        r"send\s+(us|me)\s+(a\s+)?dm",
        r"direct\s+message",
        r"private\s+(message|dm)",
        r"please\s+contact\s+(us|me)\s+(directly|privately)",
    ],
    "troubleshooting": [
        r"(try|please\s+try|try\s+to)\s+(restart|reboot|reset|clear|flush|reinstall|update)",
        r"(restart|reboot|reset)\s+(the\s+)?(app|application|device|phone|computer)",
        r"clear\s+(cache|cookies|data|browser)",
        r"uninstall\s+and\s+reinstall",
        r"check\s+(your|the)\s+(connection|settings|update)",
    ],
    "status_update": [
        r"(we\s+)?(are|have|will|can)\s+(looking|looking\s+into|investigating|checking|reviewing)",
        r"(we\s+)?(will|shall)\s+(get\s+back|update\s+you|reach\s+out)",
        r"(your\s+)?(issue|case|request)\s+(is|has\s+been)\s+(being\s+)?(reviewed|investigated|escalated)",
        r"(we\s+)?(are\s+aware|have\s+noted)",
    ],
    "refund_or_compensation_discussion": [
        r"(refund|credit|compensation|reimburse|reimbursement)",
        r"(we\s+)?(will|can|have)\s+(refund|credit|compensate)",
        r"(your\s+)?(refund|credit)\s+(is|has\s+been|will\s+be)",
    ],
    "replacement_or_rebooking_discussion": [
        r"(replacement|replace|rebook|reship|resend|new\s+(order|shipment|item))",
        r"(we\s+)?(will|can|have)\s+(send|ship|replace|resend|reship)",
        r"(a\s+)?(new|replacement)\s+(item|order|shipment)",
    ],
    "escalated": [
        r"(escalat|transfer|forward)\s+(ed|ing)?\s+(to|this|your)",
        r"(we\s+)?(have\s+)?escalat",
        r"(our\s+)?(team|specialist|manager|supervisor)\s+(will|is|are)",
        r"(looking\s+into|investigating)\s+(this\s+)?(further|more|closely)",
    ],
    "apology_only": [
        r"(we\s+)?(are\s+)?sorry\s+(for|about|to\s+hear)",
        r"(apologize|apologies)\s+(for|about|to\s+hear)",
        r"(sorry\s+for\s+the\s+inconvenience|sorry\s+for\s+the\s+trouble)",
    ],
    "information_provided": [
        r"(here\s+is|here\s+are|you\s+can\s+find|please\s+see|check\s+(out\s+)?(the|this|below))",
        r"(our\s+)?(policy|terms|guidelines|instructions)\s+(is|are|states|says)",
        r"(you\s+can|you\s+may|you\s+should)\s+(visit|check|go\s+to|see|use|try)",
        r"(link|website|page|help\s+center|support\s+page)",
    ],
}


def extract_resolution_type(support_response: str) -> tuple[str, str]:
    """Extract resolution type and evidence from support response.

    Returns:
        Tuple of (resolution_type, evidence_text)
    """
    if not support_response or not support_response.strip():
        return "no_resolution", "Empty support response"

    text = support_response.strip()
    text_lower = text.lower()

    # Check each resolution type
    for resolution_type, patterns in RESOLUTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                # Extract the matching sentence as evidence
                evidence = _extract_evidence(text, pattern)
                return resolution_type, evidence

    # Check for clear resolution signals
    if any(signal in text_lower for signal in ["resolved", "fixed", "working", "solved"]):
        return "information_provided", text[:200]

    # Default
    return "unclear", text[:200]


def _extract_evidence(text: str, pattern: str) -> str:
    """Extract the relevant sentence(s) as evidence."""
    sentences = re.split(r'[.!?]+', text)
    for sentence in sentences:
        if re.search(pattern, sentence.lower()):
            return sentence.strip()[:200]
    return text[:200]


def build_resolution_evidence(
    support_response: str,
    resolution_type: str,
) -> str:
    """Build human-readable evidence for the resolution."""
    if not support_response:
        return "No support response available."

    # Truncate if too long
    evidence = support_response[:300]

    return evidence


def build_retrieval_text(
    customer_message: str,
    support_response: str,
    resolution_type: str,
    context: str = "",
) -> str:
    """Build canonical retrieval text for embedding."""
    parts = []

    parts.append(f"Customer issue:\n{customer_message}")

    if context:
        parts.append(f"\nRelevant context:\n{context}")

    parts.append(f"\nHistorical support response:\n{support_response}")

    parts.append(f"\nHistorical resolution type:\n{resolution_type}")

    return "\n".join(parts)

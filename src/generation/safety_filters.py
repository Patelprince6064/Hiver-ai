"""Safety filters for reply content.

Detects potentially risky content in historical responses that are copied verbatim.
"""

import re
from dataclasses import dataclass, field

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+")
ORDER_ID_RE = re.compile(r"\b[A-Z]{2,5}[-_]?\d{4,12}\b")
TICKET_RE = re.compile(r"\b(?:ticket|case|reference|ref)[\s#:]*\w+\d+\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
NAME_RE = re.compile(r"\b(?:my name is|I'm|this is|speaking with)\s+[A-Z][a-z]+\b", re.IGNORECASE)


@dataclass
class SafetyFlag:
    """A safety flag detected in reply content."""

    flag_type: str
    matched_text: str
    start: int
    end: int


@dataclass
class SafetyResult:
    """Result of safety filter analysis."""

    has_risk: bool
    flags: list[str] = field(default_factory=list)
    details: list[SafetyFlag] = field(default_factory=list)


def detect_pii(text: str) -> list[SafetyFlag]:
    """Detect email addresses, phone numbers."""
    flags = []
    for m in EMAIL_RE.finditer(text):
        flags.append(SafetyFlag("email", m.group(), m.start(), m.end()))
    for m in PHONE_RE.finditer(text):
        flags.append(SafetyFlag("phone_number", m.group(), m.start(), m.end()))
    return flags


def detect_urls(text: str) -> list[SafetyFlag]:
    """Detect URLs."""
    flags = []
    for m in URL_RE.finditer(text):
        flags.append(SafetyFlag("url", m.group(), m.start(), m.end()))
    return flags


def detect_identifiers(text: str) -> list[SafetyFlag]:
    """Detect order IDs, ticket references, dates."""
    flags = []
    for m in ORDER_ID_RE.finditer(text):
        flags.append(SafetyFlag("order_id", m.group(), m.start(), m.end()))
    for m in TICKET_RE.finditer(text):
        flags.append(SafetyFlag("ticket_reference", m.group(), m.start(), m.end()))
    for m in DATE_RE.finditer(text):
        flags.append(SafetyFlag("date", m.group(), m.start(), m.end()))
    return flags


def detect_names(text: str) -> list[SafetyFlag]:
    """Detect customer name references."""
    flags = []
    for m in NAME_RE.finditer(text):
        flags.append(SafetyFlag("customer_name", m.group(), m.start(), m.end()))
    return flags


def analyze_reply_safety(reply_text: str) -> SafetyResult:
    """Analyze a reply for safety concerns.

    Args:
        reply_text: The generated reply to analyze.

    Returns:
        SafetyResult with detected flags and details.
    """
    all_details = []
    all_details.extend(detect_pii(reply_text))
    all_details.extend(detect_urls(reply_text))
    all_details.extend(detect_identifiers(reply_text))
    all_details.extend(detect_names(reply_text))

    flag_types = list({d.flag_type for d in all_details})

    risk_flags = []
    if "email" in flag_types:
        risk_flags.append("contains_email")
    if "phone_number" in flag_types:
        risk_flags.append("contains_phone_number")
    if "url" in flag_types:
        risk_flags.append("contains_url")
    if "order_id" in flag_types:
        risk_flags.append("contains_order_id")
    if "ticket_reference" in flag_types:
        risk_flags.append("contains_ticket_reference")
    if "date" in flag_types:
        risk_flags.append("contains_date")
    if "customer_name" in flag_types:
        risk_flags.append("contains_customer_name")

    return SafetyResult(
        has_risk=len(risk_flags) > 0,
        flags=risk_flags,
        details=all_details,
    )

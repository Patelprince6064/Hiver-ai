"""URL checker for grounding verification.

Detects URLs in generated replies and checks if they are supported.
"""

import re
from dataclasses import dataclass, field
from typing import Any


URL_RE = re.compile(r'https?://[^\s,;:!?\)]+|www\.[^\s,;:!?\)]+')


@dataclass
class URLClaim:
    """A URL detected in text."""

    url: str
    start: int
    end: int


@dataclass
class URLCheckResult:
    """Result of URL checking."""

    urls_found: list[URLClaim] = field(default_factory=list)
    unsupported: list[URLClaim] = field(default_factory=list)
    supported: list[URLClaim] = field(default_factory=list)
    passed: bool = True
    issues: list[str] = field(default_factory=list)


def extract_urls(text: str) -> list[URLClaim]:
    """Extract all URLs from text.

    Args:
        text: The text to analyze.

    Returns:
        List of detected URLClaim objects.
    """
    return [URLClaim(m.group(), m.start(), m.end()) for m in URL_RE.finditer(text)]


def check_urls(
    reply_text: str,
    evidence: list[dict[str, Any]],
    customer_message: str = "",
) -> URLCheckResult:
    """Check if URLs in reply are supported by evidence or customer message.

    Args:
        reply_text: The generated reply.
        evidence: List of evidence dicts from retrieval.
        customer_message: The original customer message.

    Returns:
        URLCheckResult with support status.
    """
    reply_urls = extract_urls(reply_text)

    evidence_text = " ".join(
        ev.get("support_response", "") for ev in evidence
    )

    evidence_urls = set(e.url.lower() for e in extract_urls(evidence_text))
    customer_urls = set(e.url.lower() for e in extract_urls(customer_message))

    unsupported: list[URLClaim] = []
    supported: list[URLClaim] = []

    for ru in reply_urls:
        if ru.url.lower() in evidence_urls or ru.url.lower() in customer_urls:
            supported.append(ru)
        else:
            unsupported.append(ru)

    issues = [
        f"Unsupported URL: {uu.url}" for uu in unsupported
    ]

    return URLCheckResult(
        urls_found=reply_urls,
        unsupported=unsupported,
        supported=supported,
        passed=len(unsupported) == 0,
        issues=issues,
    )

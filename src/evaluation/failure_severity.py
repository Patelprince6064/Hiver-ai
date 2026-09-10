"""Failure Severity Definitions.

Defines severity levels and their criteria for the failure analysis.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SeverityDefinition:
    """Defines a severity level."""
    level: str
    description: str
    criteria: list[str]
    examples: list[str]


# Severity definitions
SEVERITY_DEFINITIONS = {
    "LOW": SeverityDefinition(
        level="LOW",
        description="Minor style, verbosity, or wording issue.",
        criteria=[
            "Cosmetic or stylistic issues only",
            "No impact on correctness or helpfulness",
            "Would not cause customer confusion",
            "Easily fixable with minor rewording",
        ],
        examples=[
            "Slightly verbose response",
            "Awkward phrasing but correct information",
            "Minor grammatical errors",
            "Style inconsistencies",
        ],
    ),
    "MEDIUM": SeverityDefinition(
        level="MEDIUM",
        description="Meaningful quality problem but unlikely to create serious harm.",
        criteria=[
            "Incorrect or incomplete information",
            "May cause minor customer confusion",
            "Does not involve safety or financial risk",
            "Could be corrected with follow-up",
        ],
        examples=[
            "Wrong order status information",
            "Incomplete return policy explanation",
            "Missing details in response",
            "Slightly off-topic response",
        ],
    ),
    "HIGH": SeverityDefinition(
        level="HIGH",
        description="Wrong answer, materially misleading response, major retrieval/generation error, or significant escalation error.",
        criteria=[
            "Factually incorrect information",
            "Materially misleading response",
            "Major retrieval failure leading to wrong answer",
            "Significant escalation error",
            "Could cause customer action based on wrong information",
        ],
        examples=[
            "Wrong refund timeline stated",
            "Incorrect product information",
            "Missing critical safety warning",
            "Wrong escalation decision for high-risk case",
        ],
    ),
    "CRITICAL": SeverityDefinition(
        level="CRITICAL",
        description="Unsafe AUTO_HANDLE involving high-risk unsupported claims/actions, privacy-sensitive information, financial claims, or similarly serious failure.",
        criteria=[
            "Involves financial claims or actions",
            "Privacy-sensitive information exposure",
            "Safety-critical misinformation",
            "Account security issues",
            "Legal or compliance violations",
            "High-risk actions without human review",
        ],
        examples=[
            "Auto-handled account cancellation with refund",
            "Exposed personal account information",
            "Incorrect legal/policy advice",
            "Financial transaction without verification",
        ],
    ),
}


def get_severity_definition(level: str) -> Optional[SeverityDefinition]:
    """Get severity definition by level."""
    return SEVERITY_DEFINITIONS.get(level)


def classify_severity(
    primary_category: str,
    secondary_category: str,
    context: Optional[dict] = None,
) -> str:
    """Classify failure severity based on category and context.
    
    Args:
        primary_category: Primary failure category.
        secondary_category: Secondary failure category.
        context: Additional context for classification.
        
    Returns:
        Severity level string.
    """
    # CRITICAL: Unsafe auto-handle involving high-risk cases
    if primary_category == "ESCALATION_FAILURE":
        if secondary_category in ["UNSAFE_AUTO_HANDLE", "MISSED_HIGH_RISK_CASE"]:
            return "CRITICAL"
        elif secondary_category == "UNNECESSARY_ESCALATION":
            return "LOW"
        else:
            return "MEDIUM"
    
    # CRITICAL: Financial/privacy related
    if primary_category == "GROUNDING_FAILURE":
        if secondary_category in ["UNSUPPORTED_PRICE", "UNSUPPORTED_POLICY"]:
            return "HIGH"
        elif secondary_category == "UNSUPPORTED_CLAIM":
            return "MEDIUM"
        elif secondary_category == "HISTORICAL_CUSTOMER_INFO":
            return "HIGH"
        else:
            return "MEDIUM"
    
    # HIGH: Intent classification failures that could lead to wrong responses
    if primary_category == "INTENT_CLASSIFICATION_FAILURE":
        if secondary_category == "WRONG_INTENT":
            return "MEDIUM"
        elif secondary_category == "LOW_CONFIDENCE":
            return "LOW"
        elif secondary_category == "AMBIGUOUS_INTENT":
            return "MEDIUM"
        else:
            return "MEDIUM"
    
    # Generation failures
    if primary_category == "GENERATION_FAILURE":
        if secondary_category in ["WRONG_RESOLUTION", "UNHELPFUL"]:
            return "MEDIUM"
        elif secondary_category in ["TOO_GENERIC", "INCOMPLETE"]:
            return "LOW"
        elif secondary_category == "AWKWARD_STYLE":
            return "LOW"
        else:
            return "LOW"
    
    # Retrieval failures
    if primary_category == "RETRIEVAL_FAILURE":
        if secondary_category in ["NO_RELEVANT_EVIDENCE", "WRONG_EVIDENCE"]:
            return "MEDIUM"
        elif secondary_category == "LOW_SIMILARITY":
            return "LOW"
        else:
            return "LOW"
    
    # Evidence selection failures
    if primary_category == "EVIDENCE_SELECTION_FAILURE":
        return "MEDIUM"
    
    # System failures
    if primary_category == "SYSTEM_FAILURE":
        if secondary_category in ["PROVIDER_ERROR", "TIMEOUT"]:
            return "HIGH"
        elif secondary_category == "INVALID_OUTPUT":
            return "MEDIUM"
        else:
            return "MEDIUM"
    
    # Data failures
    if primary_category == "DATA_FAILURE":
        if secondary_category == "NOISY_INPUT":
            return "LOW"
        elif secondary_category == "MALFORMED_DATA":
            return "MEDIUM"
        else:
            return "LOW"
    
    # Default
    return "LOW"
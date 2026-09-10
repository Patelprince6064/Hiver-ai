"""High-risk request detection.

Detects cases involving account-specific actions, order-specific status,
refund/compensation, financial claims, personal information, and other
high-risk categories that require human review.
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HighRiskDetection:
    """Result of high-risk request detection."""

    is_high_risk: bool = False
    risk_categories: list[str] = field(default_factory=list)
    risk_details: dict[str, str] = field(default_factory=dict)
    requires_external_system: bool = False
    requires_account_action: bool = False
    requires_order_status: bool = False
    involves_financial_claim: bool = False
    involves_personal_info: bool = False
    involves_identity_verification: bool = False
    involves_refund_or_compensation: bool = False


# Patterns for high-risk detection
ACCOUNT_ACTION_PATTERNS = [
    r"\b(cancel|close|deactivate|suspend|delete)\s+(my\s+)?account\b",
    r"\b(change|update|modify)\s+(my\s+)?(email|password|address|phone|name)\b",
    r"\b(account\s+)?(security|breach|hack|compromised)\b",
    r"\b(verify|verification)\s+(my\s+)?(identity|account)\b",
    r"\b(unlink|disconnect|remove)\s+(my\s+)?(payment|card|bank)\b",
]

ORDER_STATUS_PATTERNS = [
    r"\b(order\s+)?(status|update|tracking|where\s+is|when\s+(will|is))\b",
    r"\b(ship|deliver|arrival|arrived|lost|missing|stuck)\b",
    r"\b(order\s+)?(number|#)\s*\d+\b",
    r"\b(my\s+)?order\b.*\b(not\s+arriv|still\s+wait|never\s+receiv)\b",
]

REFUND_COMPENSATION_PATTERNS = [
    r"\b(refund|reimburse|credit|compensation)\b",
    r"\b(money\s+back|return\s+my)\b",
    r"\b(charge|charged|overcharg|billing\s+error)\b",
    r"\b(dispute|chargeback)\b",
]

FINANCIAL_CLAIM_PATTERNS = [
    r"\b(price|cost|charge|fee|payment)\s+(difference|error|wrong|incorrect|over)\b",
    r"\b(promo|promo(?:tion)?|discount|coupon)\s+(code|not\s+work|didn'?t\s+work)\b",
    r"\b(unsupported\s+)?(price|guarantee|timeline|refund)\b",
]

PERSONAL_INFO_PATTERNS = [
    r"\b(my\s+)?(email|e-mail|phone|address|ssn|social\s+security)\b",
    r"\b(credit\s+card|bank\s+account|routing\s+number)\b",
    r"\b(password|passcode|pin\s+number)\b",
]

IDENTITY_VERIFICATION_PATTERNS = [
    r"\b(verify|verification)\s+(my\s+)?(identity|account|email|phone)\b",
    r"\b(prove|proof)\s+(i\s+am|i'm)\b",
    r"\b(ownership|owner)\s+(of\s+)?(account|order)\b",
]

UNSUPPORTED_PRICING_PATTERNS = [
    r"\b(guarantee|promise|assure)\s+(lowest|best|cheapest)\s+(price|deal)\b",
    r"\b(price\s+match|price\s+guarantee)\b",
    r"\b(\d+)%\s+(off|discount|save)\b",
]

UNSUPPORTED_TIMELINE_PATTERNS = [
    r"\b(guarantee|promise|assure)\s+(delivery|arrival|response)\s+(within|by|in)\s+\d+\s+(hour|day|week)\b",
    r"\b(same[\s-]?day|next[\s-]?day|instant|immediate)\s+(delivery|response|refund)\b",
]

IRREVERSIBLE_ACTION_PATTERNS = [
    r"\b(permanent(?:ly)?|irreversible|cannot\s+undo)\b",
    r"\b(delete|erase|remove)\s+(all|every|everything|my\s+data)\b",
]


def detect_high_risk_request(
    customer_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    intent: str = "",
    grounding_status: str = "",
    retrieval_status: str = "",
) -> HighRiskDetection:
    """Detect high-risk elements in a customer request.

    Args:
        customer_message: The customer's message text.
        conversation_history: Optional conversation context.
        intent: Detected intent if available.
        grounding_status: Grounding verification status.
        retrieval_status: Retrieval system status.

    Returns:
        HighRiskDetection with detected risk categories.
    """
    detection = HighRiskDetection()
    message_lower = customer_message.lower()

    # Check account action patterns
    for pattern in ACCOUNT_ACTION_PATTERNS:
        if re.search(pattern, message_lower):
            detection.requires_account_action = True
            detection.risk_categories.append("account_action")
            detection.risk_details["account_action"] = f"Pattern matched: {pattern}"
            break

    # Check order status patterns
    for pattern in ORDER_STATUS_PATTERNS:
        if re.search(pattern, message_lower):
            detection.requires_order_status = True
            detection.risk_categories.append("order_status")
            detection.risk_details["order_status"] = f"Pattern matched: {pattern}"
            break

    # Check refund/compensation patterns
    for pattern in REFUND_COMPENSATION_PATTERNS:
        if re.search(pattern, message_lower):
            detection.involves_refund_or_compensation = True
            detection.risk_categories.append("refund_compensation")
            detection.risk_details["refund_compensation"] = f"Pattern matched: {pattern}"
            break

    # Check financial claim patterns
    for pattern in FINANCIAL_CLAIM_PATTERNS:
        if re.search(pattern, message_lower):
            detection.involves_financial_claim = True
            detection.risk_categories.append("financial_claim")
            detection.risk_details["financial_claim"] = f"Pattern matched: {pattern}"
            break

    # Check personal info patterns
    for pattern in PERSONAL_INFO_PATTERNS:
        if re.search(pattern, message_lower):
            detection.involves_personal_info = True
            detection.risk_categories.append("personal_info")
            detection.risk_details["personal_info"] = f"Pattern matched: {pattern}"
            break

    # Check identity verification patterns
    for pattern in IDENTITY_VERIFICATION_PATTERNS:
        if re.search(pattern, message_lower):
            detection.involves_identity_verification = True
            detection.risk_categories.append("identity_verification")
            detection.risk_details["identity_verification"] = f"Pattern matched: {pattern}"
            break

    # Check unsupported pricing patterns
    for pattern in UNSUPPORTED_PRICING_PATTERNS:
        if re.search(pattern, message_lower):
            detection.risk_categories.append("unsupported_pricing")
            detection.risk_details["unsupported_pricing"] = f"Pattern matched: {pattern}"
            break

    # Check unsupported timeline patterns
    for pattern in UNSUPPORTED_TIMELINE_PATTERNS:
        if re.search(pattern, message_lower):
            detection.risk_categories.append("unsupported_timeline")
            detection.risk_details["unsupported_timeline"] = f"Pattern matched: {pattern}"
            break

    # Check irreversible action patterns
    for pattern in IRREVERSIBLE_ACTION_PATTERNS:
        if re.search(pattern, message_lower):
            detection.risk_categories.append("irreversible_action")
            detection.risk_details["irreversible_action"] = f"Pattern matched: {pattern}"
            break

    # Determine if external system is required
    if detection.requires_account_action or detection.requires_order_status:
        detection.requires_external_system = True

    # Overall high-risk determination
    high_risk_categories = {
        "account_action",
        "order_status",
        "refund_compensation",
        "financial_claim",
        "personal_info",
        "identity_verification",
        "unsupported_pricing",
        "unsupported_timeline",
        "irreversible_action",
    }

    detection.is_high_risk = bool(
        high_risk_categories.intersection(detection.risk_categories)
    )

    return detection


def detection_to_dict(detection: HighRiskDetection) -> dict[str, Any]:
    """Convert HighRiskDetection to a plain dict for serialization."""
    return {
        "is_high_risk": detection.is_high_risk,
        "risk_categories": detection.risk_categories,
        "risk_details": detection.risk_details,
        "requires_external_system": detection.requires_external_system,
        "requires_account_action": detection.requires_account_action,
        "requires_order_status": detection.requires_order_status,
        "involves_financial_claim": detection.involves_financial_claim,
        "involves_personal_info": detection.involves_personal_info,
        "involves_identity_verification": detection.involves_identity_verification,
        "involves_refund_or_compensation": detection.involves_refund_or_compensation,
    }

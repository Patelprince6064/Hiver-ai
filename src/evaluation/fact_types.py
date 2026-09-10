"""Fact type categories for grounding verification.

Defines categories of claims that may appear in generated replies.
"""

from enum import Enum


class FactType(str, Enum):
    """Categories of factual claims in customer-support replies."""

    INSTRUCTION = "instruction"
    POLICY = "policy"
    ACTION = "action"
    TIMELINE = "timeline"
    PRICE = "price"
    QUANTITY = "quantity"
    IDENTIFIER = "identifier"
    CONTACT_METHOD = "contact_method"
    GUARANTEE = "guarantee"
    STATUS = "status"
    RESOLUTION = "resolution"
    TECHNICAL_CLAIM = "technical_claim"
    REFUND = "refund"
    PERSONAL_INFORMATION = "personal_information"
    ACCOUNT_ACTION = "account_action"
    ORDER_STATUS = "order_status"
    FINANCIAL_CLAIM = "financial_claim"
    OTHER = "other"


HIGH_RISK_TYPES = {
    FactType.PRICE,
    FactType.REFUND,
    FactType.GUARANTEE,
    FactType.TIMELINE,
    FactType.IDENTIFIER,
    FactType.PERSONAL_INFORMATION,
    FactType.ACCOUNT_ACTION,
    FactType.ORDER_STATUS,
    FactType.FINANCIAL_CLAIM,
}

HIGH_RISK_TYPE_NAMES = {ft.value for ft in HIGH_RISK_TYPES}


def classify_fact_type(claim_text: str) -> FactType:
    """Classify a claim into a fact type category.

    Args:
        claim_text: The extracted claim text.

    Returns:
        FactType classification.
    """
    lower = claim_text.lower()

    if any(w in lower for w in ["guarantee", "warranty", "promise", "ensure"]):
        return FactType.GUARANTEE
    if any(w in lower for w in ["refund", "money back", "reimburse"]):
        return FactType.POLICY
    if any(w in lower for w in ["price", "cost", "₹", "$", "rupees", "dollars", "fee", "charge"]):
        return FactType.PRICE
    if any(w in lower for w in ["order #", "ticket #", "case #", "reference #", "tracking #"]):
        return FactType.IDENTIFIER
    if any(w in lower for w in ["please", "kindly", "you should", "you need to", "make sure to"]):
        return FactType.INSTRUCTION
    if any(w in lower for w in ["email", "phone", "call us", "contact us", "dm us", "message us"]):
        return FactType.CONTACT_METHOD
    if any(w in lower for w in ["will arrive", "will be delivered", "within", "hours", "days", "business days", "timeline"]):
        return FactType.TIMELINE
    if any(w in lower for w in ["we have", "we will", "we can", "we are", "we've"]):
        return FactType.ACTION
    if any(w in lower for w in ["status", "update", "current state", "progress"]):
        return FactType.STATUS
    if any(w in lower for w in ["resolved", "fixed", "solved", "completed", "processed"]):
        return FactType.RESOLUTION
    if any(w in lower for w in ["quantity", "amount", "total", "%", "percent"]):
        return FactType.QUANTITY
    if any(w in lower for w in ["system", "software", "version", "api", "technical"]):
        return FactType.TECHNICAL_CLAIM

    return FactType.OTHER

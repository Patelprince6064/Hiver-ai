"""Escalation reason codes.

Defines a fixed vocabulary of reason codes for escalation decisions.
"""

from enum import Enum


class ReasonCode(str, Enum):
    """Reason codes for escalation decisions."""

    LOW_INTENT_CONFIDENCE = "LOW_INTENT_CONFIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    GROUNDING_FAILURE = "GROUNDING_FAILURE"
    HIGH_RISK_CLAIM = "HIGH_RISK_CLAIM"
    UNSUPPORTED_POLICY = "UNSUPPORTED_POLICY"
    UNSUPPORTED_PRICE = "UNSUPPORTED_PRICE"
    UNSUPPORTED_TIMELINE = "UNSUPPORTED_TIMELINE"
    ACCOUNT_ACTION_REQUIRED = "ACCOUNT_ACTION_REQUIRED"
    ORDER_STATUS_REQUIRED = "ORDER_STATUS_REQUIRED"
    PERSONAL_INFORMATION_REQUIRED = "PERSONAL_INFORMATION_REQUIRED"
    FINANCIAL_CLAIM = "FINANCIAL_CLAIM"
    MULTI_INTENT = "MULTI_INTENT"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    REPEATED_UNRESOLVED = "REPEATED_UNRESOLVED"
    COMPLEX_CASE = "COMPLEX_CASE"
    UNSAFE_REPLY = "UNSAFE_REPLY"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INVALID_REPLY = "INVALID_REPLY"
    SAFETY_RISK = "SAFETY_RISK"


ALL_REASON_CODES = {rc.value for rc in ReasonCode}

ESCALATION_CODES = {
    ReasonCode.LOW_INTENT_CONFIDENCE,
    ReasonCode.INSUFFICIENT_EVIDENCE,
    ReasonCode.RETRIEVAL_FAILURE,
    ReasonCode.GROUNDING_FAILURE,
    ReasonCode.HIGH_RISK_CLAIM,
    ReasonCode.UNSUPPORTED_POLICY,
    ReasonCode.UNSUPPORTED_PRICE,
    ReasonCode.UNSUPPORTED_TIMELINE,
    ReasonCode.ACCOUNT_ACTION_REQUIRED,
    ReasonCode.ORDER_STATUS_REQUIRED,
    ReasonCode.FINANCIAL_CLAIM,
    ReasonCode.MULTI_INTENT,
    ReasonCode.AMBIGUOUS_REQUEST,
    ReasonCode.COMPLEX_CASE,
    ReasonCode.UNSAFE_REPLY,
    ReasonCode.PROVIDER_ERROR,
    ReasonCode.INVALID_REPLY,
    ReasonCode.SAFETY_RISK,
}


def get_risk_contribution(reason_code: str) -> str:
    """Get the risk level contribution for a reason code.

    Args:
        reason_code: The reason code string.

    Returns:
        'HIGH', 'MEDIUM', or 'LOW'.
    """
    high_risk_codes = {
        ReasonCode.HIGH_RISK_CLAIM.value,
        ReasonCode.UNSUPPORTED_POLICY.value,
        ReasonCode.UNSUPPORTED_PRICE.value,
        ReasonCode.UNSUPPORTED_TIMELINE.value,
        ReasonCode.FINANCIAL_CLAIM.value,
        ReasonCode.UNSAFE_REPLY.value,
        ReasonCode.PROVIDER_ERROR.value,
        ReasonCode.INVALID_REPLY.value,
    }
    medium_risk_codes = {
        ReasonCode.INSUFFICIENT_EVIDENCE.value,
        ReasonCode.GROUNDING_FAILURE.value,
        ReasonCode.RETRIEVAL_FAILURE.value,
        ReasonCode.ACCOUNT_ACTION_REQUIRED.value,
        ReasonCode.ORDER_STATUS_REQUIRED.value,
        ReasonCode.MULTI_INTENT.value,
        ReasonCode.COMPLEX_CASE.value,
        ReasonCode.SAFETY_RISK.value,
    }

    if reason_code in high_risk_codes:
        return "HIGH"
    if reason_code in medium_risk_codes:
        return "MEDIUM"
    return "LOW"

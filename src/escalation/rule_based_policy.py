"""Conservative rule-based escalation policy.

Default behavior: when uncertain, ESCALATE_TO_HUMAN.
"""

from typing import Any

from src.escalation.reason_codes import ReasonCode
from src.escalation.risk_signals import RiskSignals


class RuleBasedPolicy:
    """Conservative rule-based escalation policy.

    Checks are applied in priority order. First matching rule wins.
    """

    def __init__(
        self,
        min_intent_confidence: float = 0.70,
        require_evidence: bool = True,
        allowed_grounding_statuses: list[str] | None = None,
        require_valid_reply: bool = True,
        escalate_on_high_risk: bool = True,
        escalate_on_ambiguous: bool = True,
        escalate_on_multi_intent: bool = True,
        policy_version: str = "v1.0",
    ) -> None:
        self.min_intent_confidence = min_intent_confidence
        self.require_evidence = require_evidence
        self.allowed_grounding_statuses = allowed_grounding_statuses or ["pass"]
        self.require_valid_reply = require_valid_reply
        self.escalate_on_high_risk = escalate_on_high_risk
        self.escalate_on_ambiguous = escalate_on_ambiguous
        self.escalate_on_multi_intent = escalate_on_multi_intent
        self.policy_version = policy_version

    def evaluate(self, signals: RiskSignals) -> tuple[str, list[str]]:
        """Evaluate signals against the policy rules.

        Args:
            signals: Extracted risk signals.

        Returns:
            Tuple of (decision, reason_codes).
        """
        reason_codes: list[str] = []

        if signals.is_provider_error:
            reason_codes.append(ReasonCode.PROVIDER_ERROR.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if not signals.reply_valid:
            reason_codes.append(ReasonCode.INVALID_REPLY.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if not signals.retrieval_available:
            reason_codes.append(ReasonCode.INSUFFICIENT_EVIDENCE.value)
            if signals.retrieval_status == "error":
                reason_codes.append(ReasonCode.RETRIEVAL_FAILURE.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.grounding_status not in self.allowed_grounding_statuses:
            reason_codes.append(ReasonCode.GROUNDING_FAILURE.value)
            if signals.has_unsupported_claims:
                reason_codes.append(ReasonCode.HIGH_RISK_CLAIM.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if self.escalate_on_high_risk and signals.has_high_risk_claims:
            reason_codes.append(ReasonCode.HIGH_RISK_CLAIM.value)
            if signals.high_risk_claim_types:
                for ct in signals.high_risk_claim_types:
                    if ct == "price":
                        reason_codes.append(ReasonCode.UNSUPPORTED_PRICE.value)
                    elif ct == "timeline":
                        reason_codes.append(ReasonCode.UNSUPPORTED_TIMELINE.value)
                    elif ct == "refund":
                        reason_codes.append(ReasonCode.UNSUPPORTED_POLICY.value)
                    elif ct == "financial_claim":
                        reason_codes.append(ReasonCode.FINANCIAL_CLAIM.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.intent_confidence is not None and signals.intent_confidence < self.min_intent_confidence:
            reason_codes.append(ReasonCode.LOW_INTENT_CONFIDENCE.value)
            if signals.is_ambiguous:
                reason_codes.append(ReasonCode.AMBIGUOUS_REQUEST.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.requires_account_action:
            reason_codes.append(ReasonCode.ACCOUNT_ACTION_REQUIRED.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.requires_order_action:
            reason_codes.append(ReasonCode.ORDER_STATUS_REQUIRED.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.has_financial_claim:
            reason_codes.append(ReasonCode.FINANCIAL_CLAIM.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if self.escalate_on_multi_intent and signals.is_multi_intent:
            reason_codes.append(ReasonCode.MULTI_INTENT.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if self.escalate_on_ambiguous and signals.is_ambiguous:
            reason_codes.append(ReasonCode.AMBIGUOUS_REQUEST.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.has_safety_risk:
            reason_codes.append(ReasonCode.SAFETY_RISK.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        return "AUTO_HANDLE", reason_codes

    def get_params(self) -> dict[str, Any]:
        """Get policy parameters."""
        return {
            "policy_version": self.policy_version,
            "min_intent_confidence": self.min_intent_confidence,
            "require_evidence": self.require_evidence,
            "allowed_grounding_statuses": self.allowed_grounding_statuses,
            "require_valid_reply": self.require_valid_reply,
            "escalate_on_high_risk": self.escalate_on_high_risk,
            "escalate_on_ambiguous": self.escalate_on_ambiguous,
            "escalate_on_multi_intent": self.escalate_on_multi_intent,
        }

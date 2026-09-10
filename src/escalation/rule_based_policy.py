"""Conservative rule-based escalation policy.

Default behavior: when uncertain, ESCALATE_TO_HUMAN.

Supports both v1.0 (conservative) and v1.1 (risk-aware) policies.
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


class RiskAwarePolicy:
    """Improved risk-aware escalation policy (v1.1).

    Extends v1.0 with:
    - Confidence margin analysis
    - Retrieval quality signals
    - High-risk request detection
    - Conversation complexity
    - Repeated unresolved issue detection

    Safety gates remain: grounding failure, insufficient evidence,
    provider error, invalid reply all force escalation.
    """

    def __init__(
        self,
        min_intent_confidence: float = 0.70,
        min_confidence_margin: float = 0.15,
        require_evidence: bool = True,
        allowed_grounding_statuses: list[str] | None = None,
        require_valid_reply: bool = True,
        escalate_on_high_risk: bool = True,
        escalate_on_ambiguous: bool = True,
        escalate_on_multi_intent: bool = True,
        escalate_on_repeated_unresolved: bool = True,
        escalate_on_complex_conversation: bool = True,
        high_risk_default_escalate: bool = True,
        min_retrieval_quality: float = 0.0,
        policy_version: str = "v1.1",
    ) -> None:
        self.min_intent_confidence = min_intent_confidence
        self.min_confidence_margin = min_confidence_margin
        self.require_evidence = require_evidence
        self.allowed_grounding_statuses = allowed_grounding_statuses or ["pass"]
        self.require_valid_reply = require_valid_reply
        self.escalate_on_high_risk = escalate_on_high_risk
        self.escalate_on_ambiguous = escalate_on_ambiguous
        self.escalate_on_multi_intent = escalate_on_multi_intent
        self.escalate_on_repeated_unresolved = escalate_on_repeated_unresolved
        self.escalate_on_complex_conversation = escalate_on_complex_conversation
        self.high_risk_default_escalate = high_risk_default_escalate
        self.min_retrieval_quality = min_retrieval_quality
        self.policy_version = policy_version

    def evaluate(self, signals: RiskSignals) -> tuple[str, list[str]]:
        """Evaluate signals against the risk-aware policy rules.

        Args:
            signals: Extracted risk signals.

        Returns:
            Tuple of (decision, reason_codes).
        """
        reason_codes: list[str] = []

        # === HARD SAFETY GATES (same as v1.0) ===

        # Provider error → always escalate
        if signals.is_provider_error:
            reason_codes.append(ReasonCode.PROVIDER_ERROR.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Invalid reply → always escalate
        if not signals.reply_valid:
            reason_codes.append(ReasonCode.INVALID_REPLY.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Insufficient evidence → always escalate
        if not signals.retrieval_available:
            reason_codes.append(ReasonCode.INSUFFICIENT_EVIDENCE.value)
            if signals.retrieval_status == "error":
                reason_codes.append(ReasonCode.RETRIEVAL_FAILURE.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Grounding failure → always escalate
        if signals.grounding_status not in self.allowed_grounding_statuses:
            reason_codes.append(ReasonCode.GROUNDING_FAILURE.value)
            if signals.has_unsupported_claims:
                reason_codes.append(ReasonCode.HIGH_RISK_CLAIM.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # === HIGH-RISK DETECTION ===

        # High-risk claims from grounding → always escalate
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

        # High-risk request detection → escalate by default
        if self.high_risk_default_escalate and signals.is_high_risk_request:
            for cat in signals.high_risk_request_categories:
                if cat == "account_action":
                    reason_codes.append(ReasonCode.ACCOUNT_ACTION_REQUIRED.value)
                elif cat == "order_status":
                    reason_codes.append(ReasonCode.ORDER_STATUS_REQUIRED.value)
                elif cat == "refund_compensation":
                    reason_codes.append(ReasonCode.FINANCIAL_CLAIM.value)
                elif cat == "financial_claim":
                    reason_codes.append(ReasonCode.FINANCIAL_CLAIM.value)
                elif cat == "personal_info":
                    reason_codes.append(ReasonCode.PERSONAL_INFORMATION_REQUIRED.value)
                elif cat == "identity_verification":
                    reason_codes.append(ReasonCode.ACCOUNT_ACTION_REQUIRED.value)
            if reason_codes:
                return "ESCALATE_TO_HUMAN", reason_codes

        # === INTENT CONFIDENCE CHECKS ===

        # Low intent confidence → escalate
        if signals.intent_confidence is not None and signals.intent_confidence < self.min_intent_confidence:
            reason_codes.append(ReasonCode.LOW_INTENT_CONFIDENCE.value)
            if signals.is_ambiguous:
                reason_codes.append(ReasonCode.AMBIGUOUS_REQUEST.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Low confidence margin → escalate (NEW in v1.1)
        if (signals.confidence_margin is not None and
                signals.confidence_margin < self.min_confidence_margin and
                signals.intent_confidence is not None and
                signals.intent_confidence < 0.85):
            reason_codes.append(ReasonCode.LOW_INTENT_CONFIDENCE.value)
            if signals.is_ambiguous:
                reason_codes.append(ReasonCode.AMBIGUOUS_REQUEST.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # === ACCOUNT/ORDER ACTIONS ===

        if signals.requires_account_action:
            reason_codes.append(ReasonCode.ACCOUNT_ACTION_REQUIRED.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.requires_order_action:
            reason_codes.append(ReasonCode.ORDER_STATUS_REQUIRED.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if signals.has_financial_claim:
            reason_codes.append(ReasonCode.FINANCIAL_CLAIM.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # === MULTI-INTENT AND AMBIGUITY ===

        if self.escalate_on_multi_intent and signals.is_multi_intent:
            reason_codes.append(ReasonCode.MULTI_INTENT.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        if self.escalate_on_ambiguous and signals.is_ambiguous:
            reason_codes.append(ReasonCode.AMBIGUOUS_REQUEST.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # === NEW v1.1 CHECKS ===

        # Repeated unresolved issue → escalate
        if self.escalate_on_repeated_unresolved and signals.has_repeated_unresolved_issue:
            reason_codes.append(ReasonCode.REPEATED_UNRESOLVED.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Complex conversation → escalate
        if (self.escalate_on_complex_conversation and
                signals.conversation_complexity_level == "high"):
            reason_codes.append(ReasonCode.COMPLEX_CASE.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # Safety risk → escalate
        if signals.has_safety_risk:
            reason_codes.append(ReasonCode.SAFETY_RISK.value)
            return "ESCALATE_TO_HUMAN", reason_codes

        # === AUTO_HANDLE ===
        return "AUTO_HANDLE", reason_codes

    def get_params(self) -> dict[str, Any]:
        """Get policy parameters."""
        return {
            "policy_version": self.policy_version,
            "min_intent_confidence": self.min_intent_confidence,
            "min_confidence_margin": self.min_confidence_margin,
            "require_evidence": self.require_evidence,
            "allowed_grounding_statuses": self.allowed_grounding_statuses,
            "require_valid_reply": self.require_valid_reply,
            "escalate_on_high_risk": self.escalate_on_high_risk,
            "escalate_on_ambiguous": self.escalate_on_ambiguous,
            "escalate_on_multi_intent": self.escalate_on_multi_intent,
            "escalate_on_repeated_unresolved": self.escalate_on_repeated_unresolved,
            "escalate_on_complex_conversation": self.escalate_on_complex_conversation,
            "high_risk_default_escalate": self.high_risk_default_escalate,
            "min_retrieval_quality": self.min_retrieval_quality,
        }

"""Escalation decision engine.

Orchestrates signal extraction and policy evaluation into a single callable interface.
"""

from typing import Any

from src.escalation.escalation_schema import EscalationDecision, build_escalation_decision
from src.escalation.reason_codes import get_risk_contribution
from src.escalation.risk_signals import RiskSignals, extract_signals, signals_to_dict
from src.escalation.rule_based_policy import RuleBasedPolicy


class EscalationDecisionEngine:
    """Evaluates whether a conversation should be auto-handled or escalated.

    Usage:
        engine = EscalationDecisionEngine()
        decision = engine.evaluate(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            reply_result=reply_result,
            grounding_result=grounding_result,
        )
    """

    def __init__(self, policy: RuleBasedPolicy | None = None) -> None:
        self.policy = policy or RuleBasedPolicy()

    def evaluate(
        self,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
    ) -> EscalationDecision:
        """Evaluate pipeline outputs and return an escalation decision.

        Args:
            intent_result: Intent classification output.
            retrieval_result: Retrieval output.
            reply_result: Reply generation output.
            grounding_result: Grounding verification output.

        Returns:
            EscalationDecision with decision, reason codes, risk level, and signals.
        """
        signals = extract_signals(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            reply_result=reply_result,
            grounding_result=grounding_result,
        )

        decision, reason_codes = self.policy.evaluate(signals)

        risk_level = self._compute_risk_level(reason_codes, signals)

        confidence = 1.0 if len(reason_codes) > 0 else 0.9

        recommended_action = self._build_recommended_action(decision, reason_codes, signals)

        return build_escalation_decision(
            decision=decision,
            reason_codes=reason_codes,
            risk_level=risk_level,
            confidence=confidence,
            signals=signals_to_dict(signals),
            recommended_action=recommended_action,
            policy_version=self.policy.policy_version,
        )

    def should_auto_handle(
        self,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
    ) -> bool:
        """Check if the conversation should be auto-handled."""
        decision = self.evaluate(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            reply_result=reply_result,
            grounding_result=grounding_result,
        )
        return decision.decision == "AUTO_HANDLE"

    def should_escalate(
        self,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
    ) -> bool:
        """Check if the conversation should be escalated."""
        decision = self.evaluate(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            reply_result=reply_result,
            grounding_result=grounding_result,
        )
        return decision.decision == "ESCALATE_TO_HUMAN"

    def explain_decision(self, decision: EscalationDecision) -> str:
        """Generate a human-readable explanation of the decision."""
        parts = [f"Decision: {decision.decision}"]
        if decision.reason_codes:
            parts.append(f"Reasons: {', '.join(decision.reason_codes)}")
        parts.append(f"Risk level: {decision.risk_level}")
        parts.append(f"Recommended: {decision.recommended_action}")
        return " | ".join(parts)

    def get_reason_codes(self, decision: EscalationDecision) -> list[str]:
        """Get the reason codes from a decision."""
        return decision.reason_codes

    def _compute_risk_level(self, reason_codes: list[str], signals: RiskSignals) -> str:
        """Compute risk level from reason codes and signals."""
        if not reason_codes:
            return "LOW"

        levels = [get_risk_contribution(rc) for rc in reason_codes]

        if "HIGH" in levels:
            return "HIGH"
        if "MEDIUM" in levels:
            return "MEDIUM"
        return "LOW"

    def _build_recommended_action(
        self, decision: str, reason_codes: list[str], signals: RiskSignals,
    ) -> str:
        """Build a human-readable recommended action."""
        if decision == "AUTO_HANDLE":
            return "System can generate and send reply automatically"

        reasons = []
        if ReasonCode.INSUFFICIENT_EVIDENCE.value in reason_codes:
            reasons.append("no sufficient historical evidence available")
        if ReasonCode.GROUNDING_FAILURE.value in reason_codes:
            reasons.append("generated reply could not pass grounding verification")
        if ReasonCode.LOW_INTENT_CONFIDENCE.value in reason_codes:
            conf = signals.intent_confidence
            reasons.append(f"intent confidence ({conf:.2f}) is below threshold")
        if ReasonCode.HIGH_RISK_CLAIM.value in reason_codes:
            types = ", ".join(signals.high_risk_claim_types) if signals.high_risk_claim_types else "detected"
            reasons.append(f"high-risk unsupported claims ({types})")
        if ReasonCode.PROVIDER_ERROR.value in reason_codes:
            reasons.append("LLM provider error occurred")
        if ReasonCode.INVALID_REPLY.value in reason_codes:
            reasons.append("generated reply is empty or invalid")
        if ReasonCode.ACCOUNT_ACTION_REQUIRED.value in reason_codes:
            reasons.append("request requires account-specific action")
        if ReasonCode.ORDER_STATUS_REQUIRED.value in reason_codes:
            reasons.append("request requires order-specific action")
        if ReasonCode.FINANCIAL_CLAIM.value in reason_codes:
            reasons.append("request involves financial/refund claims")
        if ReasonCode.MULTI_INTENT.value in reason_codes:
            reasons.append("request contains multiple intents")
        if ReasonCode.AMBIGUOUS_REQUEST.value in reason_codes:
            reasons.append("request is ambiguous")
        if ReasonCode.SAFETY_RISK.value in reason_codes:
            reasons.append("safety risk detected in reply")
        if ReasonCode.RETRIEVAL_FAILURE.value in reason_codes:
            reasons.append("retrieval system failed")

        if not reasons:
            reasons.append("human review required")

        return "Escalate: " + "; ".join(reasons)


from src.escalation.reason_codes import ReasonCode

"""Escalation baseline strategies.

Provides trivial baselines for comparison:
- AlwaysAutoHandle: always returns AUTO_HANDLE
- AlwaysEscalate: always returns ESCALATE_TO_HUMAN
"""

from typing import Any

from src.escalation.escalation_schema import EscalationDecision, build_escalation_decision


class AlwaysAutoHandle:
    """Baseline: every request is auto-handled.

    This is the most aggressive strategy — it never escalates.
    Useful as a lower bound for safety.
    """

    def evaluate(
        self,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
    ) -> EscalationDecision:
        return build_escalation_decision(
            decision="AUTO_HANDLE",
            reason_codes=[],
            risk_level="LOW",
            confidence=1.0,
            signals={},
            recommended_action="Always auto-handle baseline",
            policy_version="baseline_v1",
        )

    def should_auto_handle(self, **kwargs: Any) -> bool:
        return True

    def should_escalate(self, **kwargs: Any) -> bool:
        return False

    def get_params(self) -> dict[str, Any]:
        return {"strategy": "always_auto_handle"}


class AlwaysEscalate:
    """Baseline: every request is escalated.

    This is the most conservative strategy — it never auto-handles.
    Useful as an upper bound for safety.
    """

    def evaluate(
        self,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
    ) -> EscalationDecision:
        return build_escalation_decision(
            decision="ESCALATE_TO_HUMAN",
            reason_codes=["ALWAYS_ESCALATE_BASELINE"],
            risk_level="HIGH",
            confidence=1.0,
            signals={},
            recommended_action="Always escalate baseline",
            policy_version="baseline_v1",
        )

    def should_auto_handle(self, **kwargs: Any) -> bool:
        return False

    def should_escalate(self, **kwargs: Any) -> bool:
        return True

    def get_params(self) -> dict[str, Any]:
        return {"strategy": "always_escalate"}

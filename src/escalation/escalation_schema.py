"""Escalation decision schema.

Defines the structured output for escalation decisions.
"""

from typing import Any

from pydantic import BaseModel, Field


class EscalationDecision(BaseModel):
    """Structured escalation decision output."""

    decision: str = Field(
        ...,
        description="AUTO_HANDLE or ESCALATE_TO_HUMAN",
        pattern="^(AUTO_HANDLE|ESCALATE_TO_HUMAN)$",
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="List of reason codes explaining the decision",
    )
    risk_level: str = Field(
        "LOW",
        description="LOW, MEDIUM, or HIGH",
        pattern="^(LOW|MEDIUM|HIGH)$",
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Policy confidence (deterministic, not probabilistic)",
    )
    signals: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw signal values used in the decision",
    )
    recommended_action: str = Field(
        "",
        description="Human-readable recommended action",
    )
    policy_version: str = Field(
        "v1.0",
        description="Policy version identifier",
    )


def build_escalation_decision(
    decision: str,
    reason_codes: list[str] | None = None,
    risk_level: str = "LOW",
    confidence: float = 1.0,
    signals: dict[str, Any] | None = None,
    recommended_action: str = "",
    policy_version: str = "v1.0",
) -> EscalationDecision:
    """Build an EscalationDecision from components."""
    if not recommended_action:
        if decision == "ESCALATE_TO_HUMAN":
            recommended_action = "Human review required before responding"
        else:
            recommended_action = "System can generate and send reply automatically"

    return EscalationDecision(
        decision=decision,
        reason_codes=reason_codes or [],
        risk_level=risk_level,
        confidence=confidence,
        signals=signals or {},
        recommended_action=recommended_action,
        policy_version=policy_version,
    )

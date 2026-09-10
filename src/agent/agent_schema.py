"""End-to-end agent schema.

Defines structured objects for agent requests, responses, traces, and human review packages.
"""

from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Request to the end-to-end agent."""

    message: str = Field(..., description="Customer message to process")
    conversation_id: str | None = Field(None, description="Optional conversation ID")
    message_id: str | None = Field(None, description="Optional message ID")
    conversation_context: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional conversation context (previous messages)",
    )


class AgentEvidence(BaseModel):
    """Evidence item returned by the agent."""

    knowledge_id: str = Field(..., description="Knowledge record ID")
    customer_message: str = Field("", description="Historical customer message")
    support_response: str = Field("", description="Historical support response")
    similarity_score: float = Field(0.0, description="Similarity score")
    intent: str | None = Field(None, description="Intent of the historical record")
    resolution_type: str | None = Field(None, description="Resolution type")


class AgentEscalation(BaseModel):
    """Escalation decision included in agent response."""

    decision: str = Field(..., description="AUTO_HANDLE or ESCALATE_TO_HUMAN")
    reason_codes: list[str] = Field(default_factory=list, description="Reason codes")
    risk_level: str = Field("LOW", description="LOW, MEDIUM, or HIGH")
    policy_version: str = Field("v1.1", description="Policy version")
    recommended_action: str = Field("", description="Recommended human action")


class HumanReviewPackage(BaseModel):
    """Package for human review when escalating."""

    customer_message: str = Field(..., description="Original customer message")
    conversation_id: str | None = Field(None, description="Conversation ID")
    predicted_intent: str | None = Field(None, description="Predicted intent")
    intent_confidence: float | None = Field(None, description="Intent confidence")
    retrieved_evidence: list[AgentEvidence] = Field(
        default_factory=list, description="Retrieved evidence"
    )
    draft_reply: str | None = Field(
        None, description="UNSENT DRAFT reply if available"
    )
    grounding_status: str | None = Field(None, description="Grounding verification status")
    escalation_reasons: list[str] = Field(
        default_factory=list, description="Escalation reason codes"
    )
    risk_signals: dict[str, Any] = Field(
        default_factory=dict, description="Risk signals"
    )
    recommended_action: str = Field(
        "", description="Recommended human action"
    )
    policy_version: str = Field("v1.1", description="Policy version")


class AgentResponse(BaseModel):
    """Response from the end-to-end agent."""

    decision: str = Field(
        ..., description="AUTO_HANDLE or ESCALATE_TO_HUMAN"
    )
    reply: str | None = Field(
        None, description="Generated reply (only for AUTO_HANDLE)"
    )
    intent: str | None = Field(None, description="Classified intent")
    intent_confidence: float | None = Field(None, description="Intent confidence")
    evidence: list[AgentEvidence] = Field(
        default_factory=list, description="Retrieved evidence"
    )
    grounding_status: str | None = Field(None, description="Grounding status")
    escalation: AgentEscalation = Field(
        ..., description="Escalation decision details"
    )
    human_review: HumanReviewPackage | None = Field(
        None, description="Human review package (only for ESCALATE_TO_HUMAN)"
    )
    trace_id: str = Field("", description="Trace ID for debugging")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


def build_agent_response(
    decision: str,
    reply: str | None = None,
    intent: str | None = None,
    intent_confidence: float | None = None,
    evidence: list[dict[str, Any]] | None = None,
    grounding_status: str | None = None,
    escalation_decision: str = "",
    escalation_reason_codes: list[str] | None = None,
    escalation_risk_level: str = "LOW",
    escalation_policy_version: str = "v1.1",
    escalation_recommended_action: str = "",
    human_review: dict[str, Any] | None = None,
    trace_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> AgentResponse:
    """Build an AgentResponse from components."""
    agent_evidence = []
    for e in (evidence or []):
        agent_evidence.append(AgentEvidence(
            knowledge_id=e.get("knowledge_id", ""),
            customer_message=e.get("customer_message", ""),
            support_response=e.get("support_response", ""),
            similarity_score=e.get("similarity_score", 0.0),
            intent=e.get("intent"),
            resolution_type=e.get("resolution_type"),
        ))

    escalation = AgentEscalation(
        decision=escalation_decision or decision,
        reason_codes=escalation_reason_codes or [],
        risk_level=escalation_risk_level,
        policy_version=escalation_policy_version,
        recommended_action=escalation_recommended_action,
    )

    human_review_pkg = None
    if human_review:
        human_review_pkg = HumanReviewPackage(
            customer_message=human_review.get("customer_message", ""),
            conversation_id=human_review.get("conversation_id"),
            predicted_intent=human_review.get("predicted_intent"),
            intent_confidence=human_review.get("intent_confidence"),
            retrieved_evidence=agent_evidence,
            draft_reply=human_review.get("draft_reply"),
            grounding_status=human_review.get("grounding_status"),
            escalation_reasons=human_review.get("escalation_reasons", []),
            risk_signals=human_review.get("risk_signals", {}),
            recommended_action=human_review.get("recommended_action", ""),
            policy_version=human_review.get("policy_version", "v1.1"),
        )

    return AgentResponse(
        decision=decision,
        reply=reply,
        intent=intent,
        intent_confidence=intent_confidence,
        evidence=agent_evidence,
        grounding_status=grounding_status,
        escalation=escalation,
        human_review=human_review_pkg,
        trace_id=trace_id,
        metadata=metadata or {},
    )

"""Reply generation output schema.

Defines the structured format for generated replies.
"""

from typing import Any

from pydantic import BaseModel, Field


class ReplyEvidence(BaseModel):
    """A piece of evidence supporting the reply."""

    knowledge_id: str = Field(..., description="Knowledge record ID")
    conversation_id: str | None = Field(None, description="Source conversation ID")
    source_message_id: str | None = Field(None, description="Source message ID")
    similarity_score: float = Field(..., description="Similarity score")
    support_response: str = Field(..., description="Historical support response used")
    intent: str | None = Field(None, description="Intent of the historical record")
    resolution_type: str | None = Field(None, description="Resolution type of the historical record")


class ReplyOutput(BaseModel):
    """Complete reply generation output."""

    query: str = Field(..., description="Original customer message")

    predicted_intent: str | None = Field(None, description="Classified intent")
    intent_confidence: float | None = Field(None, description="Intent classification confidence")

    reply: str | None = Field(None, description="Generated reply text")

    generation_method: str = Field(..., description="Method used: generic_baseline|historical_baseline")
    status: str = Field(..., description="success|insufficient_evidence|error")

    evidence: list[ReplyEvidence] = Field(default_factory=list, description="Supporting evidence")
    risk_flags: list[str] = Field(default_factory=list, description="Safety risk flags detected in reply")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def build_reply_output(
    query: str,
    reply: str | None,
    generation_method: str,
    status: str = "success",
    predicted_intent: str | None = None,
    intent_confidence: float | None = None,
    evidence: list[dict[str, Any]] | None = None,
    risk_flags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ReplyOutput:
    """Build a ReplyOutput from components."""
    reply_evidence = []
    for e in (evidence or []):
        reply_evidence.append(ReplyEvidence(
            knowledge_id=e.get("knowledge_id", ""),
            conversation_id=e.get("conversation_id"),
            source_message_id=e.get("source_message_id"),
            similarity_score=e.get("similarity_score", 0.0),
            support_response=e.get("support_response", ""),
            intent=e.get("intent"),
            resolution_type=e.get("resolution_type"),
        ))

    return ReplyOutput(
        query=query,
        predicted_intent=predicted_intent,
        intent_confidence=intent_confidence,
        reply=reply,
        generation_method=generation_method,
        status=status,
        evidence=reply_evidence,
        risk_flags=risk_flags or [],
        metadata=metadata or {},
    )

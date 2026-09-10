"""Retrieval result schema.

Defines the structured format for retrieval results.
"""

from typing import Any

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    """A single retrieval result."""

    rank: int = Field(..., description="Rank in results list")
    knowledge_id: str = Field(..., description="Knowledge record ID")
    conversation_id: str | None = Field(None, description="Source conversation ID")
    source_message_id: str | None = Field(None, description="Source message ID")

    customer_message: str = Field(..., description="Historical customer message")
    support_response: str = Field(..., description="Historical support response")

    intent: str | None = Field(None, description="Predicted intent")
    resolution_type: str | None = Field(None, description="Resolution type")

    similarity_score: float = Field(..., description="Similarity score")

    quality_flags: list[str] = Field(default_factory=list, description="Quality flags")
    quality_category: str = Field("usable", description="Quality category")


class RetrievalResponse(BaseModel):
    """Complete retrieval response."""

    query: str = Field(..., description="Original query")
    predicted_intent: str | None = Field(None, description="Predicted intent")
    intent_confidence: float | None = Field(None, description="Intent confidence")

    retrieval_status: str = Field("success", description="success|insufficient_evidence|error")

    results: list[RetrievalResult] = Field(default_factory=list, description="Retrieval results")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Retrieval metadata")


def build_retrieval_response(
    query: str,
    results: list[dict[str, Any]],
    predicted_intent: str | None = None,
    intent_confidence: float | None = None,
    top_k: int = 5,
    retrieval_mode: str = "semantic",
) -> RetrievalResponse:
    """Build a retrieval response from results."""
    retrieval_results = []
    for i, result in enumerate(results):
        retrieval_results.append(RetrievalResult(
            rank=i + 1,
            knowledge_id=result.get("knowledge_id", ""),
            conversation_id=result.get("conversation_id"),
            source_message_id=result.get("source_message_id"),
            customer_message=result.get("customer_message", ""),
            support_response=result.get("support_response", ""),
            intent=result.get("intent"),
            resolution_type=result.get("resolution_type"),
            similarity_score=result.get("similarity_score", 0.0),
            quality_flags=result.get("quality_flags", []),
            quality_category=result.get("quality_category", "usable"),
        ))

    status = "success" if results else "insufficient_evidence"

    return RetrievalResponse(
        query=query,
        predicted_intent=predicted_intent,
        intent_confidence=intent_confidence,
        retrieval_status=status,
        results=retrieval_results,
        metadata={
            "top_k": top_k,
            "retrieval_mode": retrieval_mode,
            "n_results": len(results),
        },
    )

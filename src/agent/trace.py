"""Structured execution trace for the agent.

Records safe metadata for debugging and auditing.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTrace:
    """Structured execution trace for a single request."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent: str | None = None
    intent_confidence: float | None = None
    retrieval_count: int = 0
    best_retrieval_score: float | None = None
    grounding_status: str | None = None
    grounding_score: float | None = None
    escalation_decision: str | None = None
    escalation_reason_codes: list[str] = field(default_factory=list)
    policy_version: str = "v1.1"
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to a plain dict for serialization.

        Excludes sensitive information like API keys, prompts, and secrets.
        """
        return {
            "trace_id": self.trace_id,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "retrieval_count": self.retrieval_count,
            "best_retrieval_score": self.best_retrieval_score,
            "grounding_status": self.grounding_status,
            "grounding_score": self.grounding_score,
            "escalation_decision": self.escalation_decision,
            "escalation_reason_codes": self.escalation_reason_codes,
            "policy_version": self.policy_version,
            "error": self.error,
            "metadata": self.metadata,
        }

    def set_intent(self, intent: str, confidence: float) -> None:
        """Record intent classification result."""
        self.intent = intent
        self.intent_confidence = confidence

    def set_retrieval(self, count: int, best_score: float | None) -> None:
        """Record retrieval result."""
        self.retrieval_count = count
        self.best_retrieval_score = best_score

    def set_grounding(self, status: str, score: float | None = None) -> None:
        """Record grounding verification result."""
        self.grounding_status = status
        self.grounding_score = score

    def set_escalation(self, decision: str, reason_codes: list[str]) -> None:
        """Record escalation decision."""
        self.escalation_decision = decision
        self.escalation_reason_codes = reason_codes

    def set_error(self, error: str) -> None:
        """Record an error."""
        self.error = error

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self.metadata[key] = value


def create_trace() -> AgentTrace:
    """Create a new agent trace."""
    return AgentTrace()

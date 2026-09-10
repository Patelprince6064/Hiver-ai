"""Judge schema for LLM-as-judge evaluation.

Defines structured input and output for the LLM judge evaluation system.
This schema is designed for blind evaluation without system identity leakage.
"""

from typing import Any

from pydantic import BaseModel, Field, computed_field


class JudgeInput(BaseModel):
    """Input to the LLM judge - contains only evaluation-relevant information.

    This schema intentionally excludes:
    - System name/model identity
    - Provider information
    - Human scores
    - Expected scores
    - Whether reply came from baseline or final system
    """

    model_config = {"frozen": True}

    judge_item_id: str = Field(..., description="Unique identifier for this judge evaluation item")
    customer_message: str = Field(..., description="Original customer message")
    conversation_context: str = Field(default="", description="Conversation context if available")
    intent: str = Field(default="", description="Predicted intent")
    intent_confidence: float | None = Field(None, description="Intent confidence score if available")
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="Retrieved evidence used for reply generation")
    candidate_reply: str = Field(..., description="Reply to evaluate")


class JudgeResult(BaseModel):
    """Output from the LLM judge evaluation.

    Contains structured scores and brief rationale.
    Overall score is recalculated locally (not from LLM output).
    """

    judge_item_id: str = Field(..., description="Unique identifier matching the input")
    relevance: int = Field(..., ge=1, le=5, description="Relevance score 1-5")
    groundedness: int = Field(..., ge=1, le=5, description="Groundedness score 1-5")
    correctness: int = Field(..., ge=1, le=5, description="Correctness score 1-5")
    helpfulness: int = Field(..., ge=1, le=5, description="Helpfulness score 1-5")
    completeness: int = Field(..., ge=1, le=5, description="Completeness score 1-5")
    style: int = Field(..., ge=1, le=5, description="Style score 1-5")
    overall: float = Field(..., ge=1.0, le=5.0, description="Overall score (mean of six dimensions)")
    failure_tags: list[str] = Field(default_factory=list, description="Failure tags if issues detected")
    short_rationale: str = Field(..., max_length=500, description="Brief evidence-based justification")
    judge_status: str = Field(default="SUCCESS", description="Status: SUCCESS, INVALID_OUTPUT, ERROR")
    judge_model: str = Field(default="", description="Model used for evaluation")

    @computed_field
    @property
    def computed_overall(self) -> float:
        """Recalculate overall score as mean of six dimensions."""
        scores = [
            self.relevance,
            self.groundedness,
            self.correctness,
            self.helpfulness,
            self.completeness,
            self.style,
        ]
        return round(sum(scores) / len(scores), 2)


class BlindMapping(BaseModel):
    """Maps anonymized system labels to actual system names for a query."""

    judge_item_id: str = Field(..., description="Judge evaluation item identifier")
    candidate_id: str = Field(..., description="Anonymized candidate label (A, B, C, D)")
    system_name: str = Field(..., description="Actual system name (NOT shown to judge)")
    seed: int = Field(42, description="Random seed used for this mapping")


class JudgeEvaluationBatch(BaseModel):
    """Batch of judge evaluations with metadata."""

    batch_id: str = Field(..., description="Unique batch identifier")
    evaluations: list[JudgeResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Batch metadata")


class JudgeReliabilityResult(BaseModel):
    """Results from judge reliability checks."""

    n_examples: int = Field(0, description="Number of examples evaluated")
    n_repeated: int = Field(0, description="Number of examples evaluated multiple times")
    score_agreement: float = Field(0.0, description="Score agreement rate")
    dimension_variance: dict[str, float] = Field(default_factory=dict, description="Variance per dimension")
    overall_variance: float = Field(0.0, description="Overall score variance")
    notes: str = Field(default="", description="Additional notes")


# Default failure tags (from Phase 14)
FAILURE_TAGS = {
    "unsupported_claim",
    "wrong_intent",
    "wrong_resolution",
    "missing_context",
    "too_generic",
    "unhelpful",
    "incomplete",
    "historical_customer_info",
    "unsupported_timeline",
    "unsupported_price",
    "unsupported_policy",
    "awkward_style",
    "too_verbose",
    "too_short",
    "retrieval_error",
    "insufficient_evidence",
    "other",
}


def validate_failure_tags(tags: list[str]) -> bool:
    """Validate that all failure tags are from the allowed set."""
    return all(tag in FAILURE_TAGS for tag in tags)
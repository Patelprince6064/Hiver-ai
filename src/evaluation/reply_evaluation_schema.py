"""Reply evaluation schema.

Defines the structured format for reply quality evaluation results.
"""

from typing import Any

from pydantic import BaseModel, Field


class ReplyQualityScores(BaseModel):
    """Six-dimension quality scores for a single reply."""

    relevance: int | None = Field(None, ge=1, le=5, description="Relevance score 1-5")
    groundedness: int | None = Field(None, ge=1, le=5, description="Groundedness score 1-5")
    correctness: int | None = Field(None, ge=1, le=5, description="Correctness score 1-5")
    helpfulness: int | None = Field(None, ge=1, le=5, description="Helpfulness score 1-5")
    completeness: int | None = Field(None, ge=1, le=5, description="Completeness score 1-5")
    style: int | None = Field(None, ge=1, le=5, description="Style score 1-5")
    overall: float | None = Field(None, ge=1.0, le=5.0, description="Overall score (mean of non-null dimensions)")

    def compute_overall(self) -> float | None:
        """Compute overall score as mean of non-null dimension scores."""
        scores = [
            self.relevance,
            self.groundedness,
            self.correctness,
            self.helpfulness,
            self.completeness,
            self.style,
        ]
        valid = [s for s in scores if s is not None]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)


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


class ReplyEvaluation(BaseModel):
    """Complete evaluation record for a single reply from a single system."""

    query_id: str = Field(..., description="Unique query identifier")
    conversation_id: str = Field("", description="Conversation identifier")
    message_id: str = Field("", description="Message identifier")
    customer_message: str = Field(..., description="Customer message text")
    intent: str = Field("", description="Predicted intent")
    split: str = Field("dev", description="Data split")

    system: str = Field(..., description="System label (System A/B/C/D or name)")
    system_name: str = Field("", description="Actual system name (for analysis, not shown to annotators)")
    reply: str | None = Field(None, description="Generated reply text")
    retrieval_status: str = Field("unknown", description="Retrieval status")
    evidence_ids: list[str] = Field(default_factory=list, description="Evidence IDs used")
    grounding_status: str = Field("unknown", description="Grounding verification status")
    grounding_score: float | None = Field(None, description="Grounding score 0-1")

    scores: ReplyQualityScores = Field(default_factory=ReplyQualityScores)
    failure_tags: list[str] = Field(default_factory=list, description="Failure tags")
    free_text_reason: str = Field("", description="Evaluator's free-text reason")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BlindMapping(BaseModel):
    """Maps anonymized system labels to actual system names for a query."""

    query_id: str = Field(..., description="Query identifier")
    mapping: dict[str, str] = Field(
        ...,
        description="Maps System A/B/C/D to actual system names",
    )
    seed: int = Field(42, description="Random seed used for this mapping")


class EvaluationManifest(BaseModel):
    """Metadata for the evaluation dataset."""

    version: str = Field("1.0", description="Manifest version")
    n_queries: int = Field(0, description="Number of evaluation queries")
    seed: int = Field(42, description="Random seed")
    splits: dict[str, int] = Field(default_factory=dict, description="Query count per split")
    intent_distribution: dict[str, int] = Field(default_factory=dict, description="Intent distribution")
    timestamp: str = Field("", description="Creation timestamp")


class PairwiseComparison(BaseModel):
    """Pairwise comparison between two systems."""

    system_a: str = Field(..., description="First system name")
    system_b: str = Field(..., description="Second system name")
    n_queries: int = Field(0, description="Number of compared queries")
    wins_a: int = Field(0, description="Queries where A > B")
    ties: int = Field(0, description="Queries where A == B")
    wins_b: int = Field(0, description="Queries where A < B")
    mean_difference: float = Field(0.0, description="Mean score difference (A - B)")
    median_difference: float = Field(0.0, description="Median score difference")
    win_rate_a: float = Field(0.0, description="Win rate for A")
    win_rate_b: float = Field(0.0, description="Win rate for B")
    tie_rate: float = Field(0.0, description="Tie rate")


class IntentQualitySummary(BaseModel):
    """Reply quality summary for a single intent."""

    intent: str = Field(..., description="Intent name")
    n_examples: int = Field(0, description="Number of examples")
    mean_overall: float | None = Field(None, description="Mean overall score")
    mean_relevance: float | None = Field(None, description="Mean relevance score")
    mean_groundedness: float | None = Field(None, description="Mean groundedness score")
    mean_helpfulness: float | None = Field(None, description="Mean helpfulness score")
    mean_correctness: float | None = Field(None, description="Mean correctness score")


class EvaluationSummary(BaseModel):
    """Aggregate evaluation summary across all systems and queries."""

    n_queries: int = Field(0, description="Total evaluation queries")
    n_replies: int = Field(0, description="Total replies evaluated")
    n_annotators: int = Field(0, description="Number of annotators")
    systems: list[str] = Field(default_factory=list, description="System names")
    system_means: dict[str, dict[str, float | None]] = Field(
        default_factory=dict,
        description="Mean scores per system per dimension",
    )
    pairwise: list[PairwiseComparison] = Field(default_factory=list)
    by_intent: list[IntentQualitySummary] = Field(default_factory=list)
    failure_tag_distribution: dict[str, int] = Field(default_factory=dict)
    inter_annotator_agreement: dict[str, float] | None = Field(
        None,
        description="Agreement metrics (if multiple annotators)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_reply_evaluation(
    query_id: str,
    customer_message: str,
    system: str,
    reply: str | None = None,
    system_name: str = "",
    intent: str = "",
    split: str = "dev",
    retrieval_status: str = "unknown",
    evidence_ids: list[str] | None = None,
    grounding_status: str = "unknown",
    grounding_score: float | None = None,
    scores: dict[str, int | float | None] | None = None,
    failure_tags: list[str] | None = None,
    free_text_reason: str = "",
    metadata: dict[str, Any] | None = None,
) -> ReplyEvaluation:
    """Build a ReplyEvaluation from component dicts."""
    quality_scores = ReplyQualityScores(
        relevance=scores.get("relevance") if scores else None,
        groundedness=scores.get("groundedness") if scores else None,
        correctness=scores.get("correctness") if scores else None,
        helpfulness=scores.get("helpfulness") if scores else None,
        completeness=scores.get("completeness") if scores else None,
        style=scores.get("style") if scores else None,
    )
    quality_scores.overall = quality_scores.compute_overall()

    return ReplyEvaluation(
        query_id=query_id,
        customer_message=customer_message,
        system=system,
        system_name=system_name,
        reply=reply,
        intent=intent,
        split=split,
        retrieval_status=retrieval_status,
        evidence_ids=evidence_ids or [],
        grounding_status=grounding_status,
        grounding_score=grounding_score,
        scores=quality_scores,
        failure_tags=failure_tags or [],
        free_text_reason=free_text_reason,
        metadata=metadata or {},
    )

"""Judge schema for future LLM-as-judge evaluation.

Defines the structured format for judge evaluation results.
"""

from typing import Any

from pydantic import BaseModel, Field


class JudgeEvaluation(BaseModel):
    """A single judge evaluation result."""

    query_id: str = Field(..., description="Unique query identifier")
    customer_message: str = Field(..., description="Original customer message")
    reply: str = Field(..., description="Generated reply")
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="Evidence used")

    groundedness: float = Field(
        ..., ge=0.0, le=1.0, description="How well the reply is grounded in evidence"
    )
    relevance: float = Field(
        ..., ge=0.0, le=1.0, description="How relevant the reply is to the customer"
    )
    helpfulness: float = Field(
        ..., ge=0.0, le=1.0, description="How helpful the reply is"
    )
    correctness: float = Field(
        ..., ge=0.0, le=1.0, description="Factual correctness of the reply"
    )
    style: float = Field(
        ..., ge=0.0, le=1.0, description="Style and tone quality"
    )

    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall quality score"
    )
    reason: str = Field(default="", description="Explanation of the evaluation")
    generation_method: str = Field(
        default="", description="Method used to generate the reply"
    )
    model: str = Field(default="", description="Model used for generation")
    prompt_version: str = Field(default="", description="Prompt version used")


class JudgeComparison(BaseModel):
    """Comparison of multiple generation methods."""

    query_id: str
    customer_message: str
    evaluations: list[JudgeEvaluation] = Field(default_factory=list)
    best_method: str = Field(default="")
    comparison_notes: str = Field(default="")

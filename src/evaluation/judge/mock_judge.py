"""Mock Judge implementation.

Provides deterministic evaluation for testing without API calls.
"""

import hashlib
import json
from typing import Any

from src.evaluation.judge.base_judge import BaseJudge
from src.evaluation.judge_schema import JudgeInput, JudgeResult


class MockJudge(BaseJudge):
    """Mock judge that returns deterministic scores.

    Uses input hashing to generate consistent scores for the same input.
    """

    def __init__(self, seed: int = 42) -> None:
        """Initialize the mock judge.

        Args:
            seed: Random seed for consistency.
        """
        self.seed = seed
        self._call_count = 0
        self._total_latency_ms = 0.0

    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        """Evaluate using deterministic mock scoring.

        Args:
            judge_input: Structured input for evaluation.

        Returns:
            Deterministic evaluation result.
        """
        import time

        start_time = time.time()

        if not self.validate_input(judge_input):
            return JudgeResult(
                judge_item_id=judge_input.judge_item_id,
                relevance=1,
                groundedness=1,
                correctness=1,
                helpfulness=1,
                completeness=1,
                style=1,
                overall=1.0,
                failure_tags=["other"],
                short_rationale="Invalid input provided.",
                judge_status="ERROR",
                judge_model="mock-judge",
            )

        # Generate deterministic scores based on input hash
        hash_input = f"{judge_input.judge_item_id}:{judge_input.customer_message}:{judge_input.candidate_reply}:{self.seed}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Generate scores 1-5 with realistic distribution
        # Use hash to create biased but deterministic scores
        base_score = (hash_value % 40) / 10.0 + 1.0  # 1.0 to 5.0

        # Add some variance per dimension
        scores = {}
        for i, dim in enumerate(["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]):
            dim_hash = int(hashlib.sha256(f"{hash_value}:{dim}".encode()).hexdigest(), 16)
            # Create score between 1-5 with most scores in 3-4 range
            dim_score = min(5, max(1, int(base_score + (dim_hash % 3) - 1)))
            scores[dim] = dim_score

        # Determine failure tags based on low scores
        failure_tags = []
        if scores["groundedness"] <= 2:
            failure_tags.append("unsupported_claim")
        if scores["relevance"] <= 2:
            failure_tags.append("wrong_intent")
        if scores["helpfulness"] <= 2:
            failure_tags.append("unhelpful")
        if scores["completeness"] <= 2:
            failure_tags.append("incomplete")
        if scores["style"] <= 2:
            failure_tags.append("awkward_style")

        # Generate rationale based on scores
        avg_score = sum(scores.values()) / len(scores)
        if avg_score >= 4:
            rationale = "Reply directly addresses the request and is supported by the retrieved historical evidence."
        elif avg_score >= 3:
            rationale = "Reply is generally appropriate but has some minor issues with evidence support or completeness."
        else:
            rationale = "Reply has significant issues with evidence support, relevance, or helpfulness."

        # Calculate overall score
        overall = round(sum(scores.values()) / len(scores), 2)

        # Simulate latency
        latency_ms = 10.0 + (hash_value % 20)
        self._call_count += 1
        self._total_latency_ms += latency_ms

        return JudgeResult(
            judge_item_id=judge_input.judge_item_id,
            relevance=scores["relevance"],
            groundedness=scores["groundedness"],
            correctness=scores["correctness"],
            helpfulness=scores["helpfulness"],
            completeness=scores["completeness"],
            style=scores["style"],
            overall=overall,
            failure_tags=failure_tags,
            short_rationale=rationale,
            judge_status="SUCCESS",
            judge_model="mock-judge",
        )

    def get_stats(self) -> dict[str, Any]:
        """Return judge statistics."""
        return {
            "model": "mock-judge",
            "call_count": self._call_count,
            "total_latency_ms": self._total_latency_ms,
            "avg_latency_ms": self._total_latency_ms / max(self._call_count, 1),
        }
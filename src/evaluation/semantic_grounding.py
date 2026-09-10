"""Semantic grounding check using embeddings.

Estimates whether generated sentences are semantically supported by evidence.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SemanticGroundingResult:
    """Result of semantic grounding check."""

    overall_score: float = 0.0
    sentence_scores: list[float] = field(default_factory=list)
    passed: bool = True
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def check_semantic_grounding(
    reply_text: str,
    evidence: list[dict[str, Any]],
    embedder=None,
    threshold: float | None = None,
) -> SemanticGroundingResult:
    """Check semantic grounding of reply against evidence.

    Args:
        reply_text: The generated reply.
        evidence: List of evidence dicts from retrieval.
        embedder: Optional sentence-transformer embedder. If None, uses overlap heuristic.
        threshold: Optional similarity threshold. If None, uses heuristic.

    Returns:
        SemanticGroundingResult with similarity scores.
    """
    if not reply_text or not reply_text.strip():
        return SemanticGroundingResult(
            overall_score=0.0,
            passed=False,
            issues=["Empty reply"],
        )

    if not evidence:
        return SemanticGroundingResult(
            overall_score=0.0,
            passed=False,
            issues=["No evidence to compare against"],
        )

    if embedder is not None:
        return _check_with_embeddings(reply_text, evidence, embedder, threshold)

    return _check_with_heuristic(reply_text, evidence)


def _check_with_embeddings(
    reply_text: str,
    evidence: list[dict[str, Any]],
    embedder,
    threshold: float | None,
) -> SemanticGroundingResult:
    """Check grounding using embedding similarity."""
    try:
        sentences = [s.strip() for s in reply_text.split('.') if s.strip()]
        if not sentences:
            sentences = [reply_text]

        evidence_texts = []
        for ev in evidence:
            sr = ev.get("support_response", "")
            if sr:
                evidence_texts.append(sr)

        if not evidence_texts:
            return SemanticGroundingResult(
                overall_score=0.0,
                passed=False,
                issues=["No evidence text available"],
            )

        reply_embeddings = embedder.encode(sentences)
        evidence_embeddings = embedder.encode(evidence_texts)

        sentence_scores = []
        for r_emb in reply_embeddings:
            scores = [cosine_similarity(r_emb, e_emb) for e_emb in evidence_embeddings]
            sentence_scores.append(max(scores) if scores else 0.0)

        overall_score = float(np.mean(sentence_scores)) if sentence_scores else 0.0

        effective_threshold = threshold if threshold is not None else 0.3
        passed = overall_score >= effective_threshold

        issues = []
        if not passed:
            issues.append(f"Overall semantic score {overall_score:.2f} below threshold {effective_threshold:.2f}")

        return SemanticGroundingResult(
            overall_score=overall_score,
            sentence_scores=sentence_scores,
            passed=passed,
            issues=issues,
            details={"method": "embedding", "threshold": effective_threshold},
        )
    except Exception as e:
        return SemanticGroundingResult(
            overall_score=0.0,
            passed=False,
            issues=[f"Embedding check failed: {str(e)}"],
        )


def _check_with_heuristic(
    reply_text: str,
    evidence: list[dict[str, Any]],
) -> SemanticGroundingResult:
    """Check grounding using token overlap heuristic."""
    reply_tokens = set(reply_text.lower().split())

    evidence_text = " ".join(
        ev.get("support_response", "") for ev in evidence
    )
    evidence_tokens = set(evidence_text.lower().split())

    if not reply_tokens:
        return SemanticGroundingResult(
            overall_score=0.0,
            passed=False,
            issues=["Empty reply tokens"],
        )

    overlap = reply_tokens & evidence_tokens
    score = len(overlap) / len(reply_tokens) if reply_tokens else 0.0

    passed = score >= 0.2

    issues = []
    if not passed:
        issues.append(f"Token overlap score {score:.2f} below threshold 0.20")

    return SemanticGroundingResult(
        overall_score=score,
        sentence_scores=[score],
        passed=passed,
        issues=issues,
        details={"method": "token_overlap", "threshold": 0.2},
    )

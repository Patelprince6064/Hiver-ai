"""Automated reply metrics.

Supplementary diagnostics for reply quality evaluation.
These are NOT substitutes for human quality evaluation.
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutomatedReplyMetrics:
    """Automated metrics for a single reply."""

    n_characters: int = 0
    n_words: int = 0
    n_sentences: int = 0
    has_evidence_support: bool = False
    grounding_pass: bool = False
    grounding_status: str = "unknown"
    risk_flags: list[str] = field(default_factory=list)
    has_risk: bool = False
    retrieval_status: str = "unknown"
    top_similarity: float | None = None
    is_empty: bool = False
    is_insufficient_evidence: bool = False
    evidence_count: int = 0
    generation_method: str = ""


@dataclass
class AggregateAutomatedMetrics:
    """Aggregate automated metrics across multiple replies."""

    n_replies: int = 0
    mean_length_chars: float = 0.0
    mean_length_words: float = 0.0
    mean_n_sentences: float = 0.0
    empty_rate: float = 0.0
    insufficient_evidence_rate: float = 0.0
    grounding_pass_rate: float = 0.0
    risk_rate: float = 0.0
    retrieval_success_rate: float = 0.0
    mean_top_similarity: float = 0.0
    evidence_utilization_rate: float = 0.0
    provider_error_rate: float = 0.0
    generation_method_distribution: dict[str, int] = field(default_factory=dict)


SENTENCE_SPLIT_RE = re.compile(r'[.!?\n]+')


def compute_reply_metrics(
    reply: str | None,
    evidence: list[dict[str, Any]] | None = None,
    grounding_status: str = "unknown",
    grounding_score: float | None = None,
    risk_flags: list[str] | None = None,
    retrieval_status: str = "unknown",
    top_similarity: float | None = None,
    generation_method: str = "",
) -> AutomatedReplyMetrics:
    """Compute automated metrics for a single reply.

    Args:
        reply: The generated reply text.
        evidence: List of evidence dicts used.
        grounding_status: Grounding verification status.
        grounding_score: Grounding score 0-1.
        risk_flags: List of risk flags.
        retrieval_status: Retrieval status.
        top_similarity: Top retrieval similarity score.
        generation_method: How the reply was generated.

    Returns:
        AutomatedReplyMetrics with computed metrics.
    """
    if reply is None:
        return AutomatedReplyMetrics(
            is_empty=True,
            is_insufficient_evidence=True,
            grounding_status=grounding_status,
            grounding_pass=grounding_status == "pass",
            risk_flags=risk_flags or [],
            has_risk=bool(risk_flags),
            retrieval_status=retrieval_status,
            top_similarity=top_similarity,
            generation_method=generation_method,
        )

    reply = reply.strip()
    is_empty = len(reply) == 0
    is_insufficient = reply.upper() == "INSUFFICIENT_EVIDENCE"

    words = reply.split()
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(reply) if s.strip()]

    return AutomatedReplyMetrics(
        n_characters=len(reply),
        n_words=len(words),
        n_sentences=len(sentences),
        has_evidence_support=bool(evidence),
        grounding_pass=grounding_status == "pass",
        grounding_status=grounding_status,
        risk_flags=risk_flags or [],
        has_risk=bool(risk_flags),
        retrieval_status=retrieval_status,
        top_similarity=top_similarity,
        is_empty=is_empty,
        is_insufficient_evidence=is_insufficient,
        evidence_count=len(evidence) if evidence else 0,
        generation_method=generation_method,
    )


def compute_aggregate_metrics(
    metrics_list: list[AutomatedReplyMetrics],
) -> AggregateAutomatedMetrics:
    """Compute aggregate metrics across multiple replies.

    Args:
        metrics_list: List of per-reply metrics.

    Returns:
        AggregateAutomatedMetrics with aggregated values.
    """
    if not metrics_list:
        return AggregateAutomatedMetrics()

    n = len(metrics_list)

    total_chars = sum(m.n_characters for m in metrics_list)
    total_words = sum(m.n_words for m in metrics_list)
    total_sentences = sum(m.n_sentences for m in metrics_list)

    n_empty = sum(1 for m in metrics_list if m.is_empty)
    n_insufficient = sum(1 for m in metrics_list if m.is_insufficient_evidence)
    n_grounding_pass = sum(1 for m in metrics_list if m.grounding_pass)
    n_risky = sum(1 for m in metrics_list if m.has_risk)
    n_retrieval_success = sum(1 for m in metrics_list if m.retrieval_status == "success")
    n_error = sum(1 for m in metrics_list if m.grounding_status == "error")
    n_with_evidence = sum(1 for m in metrics_list if m.evidence_count > 0)

    similarities = [m.top_similarity for m in metrics_list if m.top_similarity is not None]
    mean_sim = sum(similarities) / len(similarities) if similarities else 0.0

    method_dist: dict[str, int] = {}
    for m in metrics_list:
        method = m.generation_method or "unknown"
        method_dist[method] = method_dist.get(method, 0) + 1

    return AggregateAutomatedMetrics(
        n_replies=n,
        mean_length_chars=total_chars / n,
        mean_length_words=total_words / n,
        mean_n_sentences=total_sentences / n,
        empty_rate=n_empty / n,
        insufficient_evidence_rate=n_insufficient / n,
        grounding_pass_rate=n_grounding_pass / n,
        risk_rate=n_risky / n,
        retrieval_success_rate=n_retrieval_success / n,
        mean_top_similarity=mean_sim,
        evidence_utilization_rate=n_with_evidence / n,
        provider_error_rate=n_error / n,
        generation_method_distribution=method_dist,
    )

"""Retrieval evaluation metrics.

Calculates Recall@K, MRR, and Precision@K for retrieval evaluation.
"""

import numpy as np


def recall_at_k(relevant_ids: list[str], retrieved_ids: list[str], k: int) -> float:
    """Calculate Recall@K.

    Args:
        relevant_ids: List of relevant knowledge IDs
        retrieved_ids: List of retrieved knowledge IDs (ordered by rank)
        k: Number of top results to consider

    Returns:
        Recall@K score (0.0 or 1.0 for single-query)
    """
    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    retrieved_relevant = sum(1 for rid in top_k if rid in relevant_set)

    return min(retrieved_relevant / len(relevant_set), 1.0)


def precision_at_k(relevant_ids: list[str], retrieved_ids: list[str], k: int) -> float:
    """Calculate Precision@K.

    Args:
        relevant_ids: List of relevant knowledge IDs
        retrieved_ids: List of retrieved knowledge IDs (ordered by rank)
        k: Number of top results to consider

    Returns:
        Precision@K score
    """
    if not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    retrieved_relevant = sum(1 for rid in top_k if rid in relevant_set)

    return retrieved_relevant / len(top_k)


def mean_reciprocal_rank(relevant_ids: list[str], retrieved_ids: list[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) for a single query.

    Args:
        relevant_ids: List of relevant knowledge IDs
        retrieved_ids: List of retrieved knowledge IDs (ordered by rank)

    Returns:
        Reciprocal rank (1/rank of first relevant result, or 0.0)
    """
    relevant_set = set(relevant_ids)

    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_set:
            return 1.0 / (i + 1)

    return 0.0


def evaluate_retrieval(
    queries: list[dict],
    retriever_fn,
    k_values: list[int] = [1, 3, 5, 10],
) -> dict:
    """Evaluate retrieval across multiple queries.

    Args:
        queries: List of query dicts with 'query_text' and 'relevant_knowledge_ids'
        retriever_fn: Function that takes query_text and returns retrieved IDs
        k_values: List of K values to evaluate

    Returns:
        Dictionary of metrics
    """
    all_recall = {k: [] for k in k_values}
    all_precision = {k: [] for k in k_values}
    all_mrr = []

    for query in queries:
        query_text = query.get("query_text", "")
        relevant_ids = query.get("relevant_knowledge_ids", [])

        retrieved = retriever_fn(query_text)
        retrieved_ids = [r.get("knowledge_id", "") for r in retrieved]

        for k in k_values:
            all_recall[k].append(recall_at_k(relevant_ids, retrieved_ids, k))
            all_precision[k].append(precision_at_k(relevant_ids, retrieved_ids, k))

        all_mrr.append(mean_reciprocal_rank(relevant_ids, retrieved_ids))

    results = {}
    for k in k_values:
        results[f"recall@{k}"] = float(np.mean(all_recall[k]))
        results[f"precision@{k}"] = float(np.mean(all_precision[k]))

    results["mrr"] = float(np.mean(all_mrr))
    results["n_queries"] = len(queries)

    return results

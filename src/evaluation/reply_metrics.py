"""Reply evaluation metrics.

Calculates objective metrics for reply baseline evaluation.
"""

import numpy as np


def response_coverage(predictions: list[dict]) -> float:
    """Percentage of queries that produced a non-null reply.

    Args:
        predictions: List of prediction dicts with 'reply' field.

    Returns:
        Coverage fraction [0, 1].
    """
    if not predictions:
        return 0.0
    has_reply = sum(1 for p in predictions if p.get("reply") is not None)
    return has_reply / len(predictions)


def evidence_availability(predictions: list[dict]) -> float:
    """Percentage of queries with at least one evidence item.

    Args:
        predictions: List of prediction dicts with 'evidence' field.

    Returns:
        Availability fraction [0, 1].
    """
    if not predictions:
        return 0.0
    has_evidence = sum(1 for p in predictions if p.get("evidence"))
    return has_evidence / len(predictions)


def similarity_distribution(predictions: list[dict]) -> dict[str, float]:
    """Distribution of top retrieval similarity scores.

    Args:
        predictions: List of prediction dicts with 'evidence' field.

    Returns:
        Dict with mean, median, min, max, std of top similarity scores.
    """
    scores = []
    for p in predictions:
        evidence = p.get("evidence", [])
        if evidence:
            scores.append(evidence[0].get("similarity_score", 0.0))

    if not scores:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

    arr = np.array(scores)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)),
    }


def intent_consistency(predictions: list[dict]) -> float:
    """Percentage where retrieved evidence intent matches predicted intent.

    Args:
        predictions: List of prediction dicts with 'predicted_intent' and 'evidence'.

    Returns:
        Consistency fraction [0, 1].
    """
    if not predictions:
        return 0.0

    matches = 0
    count = 0
    for p in predictions:
        predicted = p.get("predicted_intent")
        evidence = p.get("evidence", [])
        if predicted and evidence:
            count += 1
            evidence_intent = evidence[0].get("intent")
            if evidence_intent == predicted:
                matches += 1

    return matches / count if count > 0 else 0.0


# Resolution intent compatibility mapping
RESOLUTION_INTENT_COMPAT = {
    "order_status": {"delivery_delay", "order_status", "shipping", "missing_order", "order_issue"},
    "delivery_delay": {"delivery_delay", "shipping", "missing_order", "order_status", "order_issue"},
    "refund_request": {"refund", "cancellation", "order_issue", "complaint"},
    "product_inquiry": {"product_inquiry", "general_question", "store_location"},
    "complaint": {"complaint", "refund", "cancellation", "order_issue"},
    "technical_support": {"technical_support", "account_issue", "billing"},
    "account_issue": {"account_issue", "technical_support", "billing"},
    "cancellation": {"cancellation", "refund", "complaint"},
    "billing": {"billing", "account_issue", "technical_support"},
}


def resolution_consistency(predictions: list[dict]) -> float:
    """Percentage where retrieved resolution type is compatible with predicted intent.

    Args:
        predictions: List of prediction dicts with 'predicted_intent' and 'evidence'.

    Returns:
        Consistency fraction [0, 1].
    """
    if not predictions:
        return 0.0

    compatible = 0
    count = 0
    for p in predictions:
        predicted_intent = p.get("predicted_intent")
        evidence = p.get("evidence", [])
        if predicted_intent and evidence:
            count += 1
            resolution = evidence[0].get("resolution_type")
            if resolution in RESOLUTION_INTENT_COMPAT.get(predicted_intent, set()):
                compatible += 1

    return compatible / count if count > 0 else 0.0


def safety_risk_rate(predictions: list[dict]) -> float:
    """Percentage of replies with safety risk flags.

    Args:
        predictions: List of prediction dicts with 'risk_flags' field.

    Returns:
        Risk rate fraction [0, 1].
    """
    if not predictions:
        return 0.0
    has_risk = sum(1 for p in predictions if p.get("risk_flags"))
    return has_risk / len(predictions)


def reply_length_distribution(predictions: list[dict]) -> dict[str, float]:
    """Distribution of reply lengths (word count).

    Args:
        predictions: List of prediction dicts with 'reply' field.

    Returns:
        Dict with mean, median, min, max word counts.
    """
    lengths = []
    for p in predictions:
        reply = p.get("reply")
        if reply:
            lengths.append(len(reply.split()))

    if not lengths:
        return {"mean": 0, "median": 0, "min": 0, "max": 0}

    arr = np.array(lengths)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def evaluate_reply_baselines(
    generic_predictions: list[dict],
    historical_predictions: list[dict],
) -> dict:
    """Evaluate both reply baselines.

    Args:
        generic_predictions: List of prediction dicts from generic baseline.
        historical_predictions: List of prediction dicts from historical baseline.

    Returns:
        Dict with metrics for both baselines.
    """
    generic_metrics = {
        "n_queries": len(generic_predictions),
        "response_coverage": response_coverage(generic_predictions),
        "evidence_availability": evidence_availability(generic_predictions),
        "intent_consistency": intent_consistency(generic_predictions),
        "safety_risk_rate": safety_risk_rate(generic_predictions),
        "reply_length": reply_length_distribution(generic_predictions),
    }

    historical_metrics = {
        "n_queries": len(historical_predictions),
        "response_coverage": response_coverage(historical_predictions),
        "evidence_availability": evidence_availability(historical_predictions),
        "similarity_distribution": similarity_distribution(historical_predictions),
        "intent_consistency": intent_consistency(historical_predictions),
        "resolution_consistency": resolution_consistency(historical_predictions),
        "safety_risk_rate": safety_risk_rate(historical_predictions),
        "reply_length": reply_length_distribution(historical_predictions),
    }

    return {
        "generic_baseline": generic_metrics,
        "historical_baseline": historical_metrics,
    }

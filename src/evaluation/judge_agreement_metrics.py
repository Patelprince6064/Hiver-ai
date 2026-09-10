"""Judge agreement metrics.

Calculates agreement metrics between human and LLM judge scores.
"""

import math
from typing import Any


def calculate_mae(human_scores: list[float], llm_scores: list[float]) -> float:
    """Calculate Mean Absolute Error.

    Args:
        human_scores: List of human scores.
        llm_scores: List of LLM scores.

    Returns:
        Mean Absolute Error.
    """
    if not human_scores or not llm_scores or len(human_scores) != len(llm_scores):
        return 0.0

    n = len(human_scores)
    return sum(abs(h - l) for h, l in zip(human_scores, llm_scores)) / n


def calculate_exact_agreement(human_scores: list[float], llm_scores: list[float]) -> float:
    """Calculate exact agreement rate.

    Args:
        human_scores: List of human scores.
        llm_scores: List of LLM scores.

    Returns:
        Exact agreement rate (0-1).
    """
    if not human_scores or not llm_scores or len(human_scores) != len(llm_scores):
        return 0.0

    n = len(human_scores)
    agreements = sum(1 for h, l in zip(human_scores, llm_scores) if h == l)
    return agreements / n


def calculate_within_1_agreement(human_scores: list[float], llm_scores: list[float]) -> float:
    """Calculate within-1 agreement rate.

    Args:
        human_scores: List of human scores.
        llm_scores: List of LLM scores.

    Returns:
        Within-1 agreement rate (0-1).
    """
    if not human_scores or not llm_scores or len(human_scores) != len(llm_scores):
        return 0.0

    n = len(human_scores)
    agreements = sum(1 for h, l in zip(human_scores, llm_scores) if abs(h - l) <= 1)
    return agreements / n


def calculate_spearman_correlation(x: list[float], y: list[float]) -> tuple[float, float]:
    """Calculate Spearman rank correlation.

    Args:
        x: First set of scores.
        y: Second set of scores.

    Returns:
        Tuple of (correlation, p-value approximation).
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0

    def rank_data(data):
        sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0.0] * len(data)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank
        return ranks

    rank_x = rank_data(x)
    rank_y = rank_data(y)

    # Calculate Pearson on ranks
    mean_rx = sum(rank_x) / n
    mean_ry = sum(rank_y) / n

    cov_rx_ry = sum((rx - mean_rx) * (ry - mean_ry) for rx, ry in zip(rank_x, rank_y)) / n
    std_rx = math.sqrt(sum((rx - mean_rx) ** 2 for rx in rank_x) / n)
    std_ry = math.sqrt(sum((ry - mean_ry) ** 2 for ry in rank_y) / n)

    if std_rx == 0 or std_ry == 0:
        spearman = 0.0
    else:
        spearman = cov_rx_ry / (std_rx * std_ry)

    # Approximate p-value using t-distribution
    if abs(spearman) >= 1.0:
        p_value = 0.0
    elif n <= 3:
        p_value = 1.0
    else:
        t_stat = spearman * math.sqrt((n - 2) / (1 - spearman ** 2))
        # Rough approximation
        df = n - 2
        p_value = max(0.001, min(1.0, 2 * math.exp(-0.5 * abs(t_stat))))

    return spearman, p_value


def calculate_pearson_correlation(x: list[float], y: list[float]) -> tuple[float, float]:
    """Calculate Pearson correlation.

    Args:
        x: First set of scores.
        y: Second set of scores.

    Returns:
        Tuple of (correlation, p-value approximation).
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)

    if std_x == 0 or std_y == 0:
        pearson = 0.0
    else:
        pearson = cov_xy / (std_x * std_y)

    # Approximate p-value
    if abs(pearson) >= 1.0:
        p_value = 0.0
    elif n <= 3:
        p_value = 1.0
    else:
        t_stat = pearson * math.sqrt((n - 2) / (1 - pearson ** 2))
        df = n - 2
        p_value = max(0.001, min(1.0, 2 * math.exp(-0.5 * abs(t_stat))))

    return pearson, p_value


def calculate_weighted_kappa(
    human_scores: list[int],
    llm_scores: list[int],
    weights: str = "linear",
) -> float:
    """Calculate weighted Cohen's kappa for ordinal ratings.

    Args:
        human_scores: List of human scores (integers 1-5).
        llm_scores: List of LLM scores (integers 1-5).
        weights: Weighting scheme ("linear" or "quadratic").

    Returns:
        Weighted kappa value.
    """
    if not human_scores or not llm_scores or len(human_scores) != len(llm_scores):
        return 0.0

    n = len(human_scores)
    if n < 2:
        return 0.0

    # Ensure scores are integers
    human_int = [int(round(h)) for h in human_scores]
    llm_int = [int(round(l)) for l in llm_scores]

    # Find min and max
    all_scores = human_int + llm_int
    min_score = min(all_scores)
    max_score = max(all_scores)
    n_categories = max_score - min_score + 1

    if n_categories < 2:
        return 1.0  # Perfect agreement if only one category

    # Create confusion matrix
    confusion = [[0] * n_categories for _ in range(n_categories)]
    for h, l in zip(human_int, llm_int):
        confusion[h - min_score][l - min_score] += 1

    # Calculate weights
    def get_weight(i, j):
        if weights == "quadratic":
            return ((i - j) ** 2) / ((n_categories - 1) ** 2)
        else:  # linear
            return abs(i - j) / (n_categories - 1)

    # Calculate weighted observed agreement
    po = 0.0
    for i in range(n_categories):
        for j in range(n_categories):
            po += (1 - get_weight(i, j)) * confusion[i][j]
    po /= n

    # Calculate expected agreement
    pe = 0.0
    row_sums = [sum(row) for row in confusion]
    col_sums = [sum(confusion[i][j] for i in range(n_categories)) for j in range(n_categories)]

    for i in range(n_categories):
        for j in range(n_categories):
            pe += (1 - get_weight(i, j)) * row_sums[i] * col_sums[j]
    pe /= (n * n)

    # Calculate kappa
    if pe >= 1.0:
        return 1.0

    kappa = (po - pe) / (1 - pe)
    return kappa


def calculate_agreement_metrics(
    human_scores: list[float],
    llm_scores: list[float],
) -> dict[str, Any]:
    """Calculate comprehensive agreement metrics.

    Args:
        human_scores: List of human scores.
        llm_scores: List of LLM scores.

    Returns:
        Dictionary of agreement metrics.
    """
    if not human_scores or not llm_scores:
        return {
            "n": 0,
            "mae": 0.0,
            "exact_agreement": 0.0,
            "within_1_agreement": 0.0,
            "spearman": 0.0,
            "spearman_p_value": 1.0,
            "pearson": 0.0,
            "pearson_p_value": 1.0,
            "weighted_kappa": 0.0,
            "human_mean": 0.0,
            "llm_mean": 0.0,
            "mean_difference": 0.0,
        }

    n = len(human_scores)
    mae = calculate_mae(human_scores, llm_scores)
    exact_agreement = calculate_exact_agreement(human_scores, llm_scores)
    within_1_agreement = calculate_within_1_agreement(human_scores, llm_scores)
    spearman, spearman_p = calculate_spearman_correlation(human_scores, llm_scores)
    pearson, pearson_p = calculate_pearson_correlation(human_scores, llm_scores)

    # Weighted kappa requires integer scores
    human_int = [int(round(h)) for h in human_scores]
    llm_int = [int(round(l)) for l in llm_scores]
    weighted_kappa = calculate_weighted_kappa(human_int, llm_int)

    human_mean = sum(human_scores) / n
    llm_mean = sum(llm_scores) / n
    mean_difference = llm_mean - human_mean

    return {
        "n": n,
        "mae": round(mae, 4),
        "exact_agreement": round(exact_agreement, 4),
        "within_1_agreement": round(within_1_agreement, 4),
        "spearman": round(spearman, 4),
        "spearman_p_value": round(spearman_p, 4),
        "pearson": round(pearson, 4),
        "pearson_p_value": round(pearson_p, 4),
        "weighted_kappa": round(weighted_kappa, 4),
        "human_mean": round(human_mean, 4),
        "llm_mean": round(llm_mean, 4),
        "mean_difference": round(mean_difference, 4),
    }


def calculate_dimension_agreement(
    dataset: list[dict],
    dimensions: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Calculate agreement for each dimension.

    Args:
        dataset: Matched evaluation dataset.
        dimensions: List of dimensions to evaluate.

    Returns:
        Dictionary of dimension-level agreement metrics.
    """
    if dimensions is None:
        dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]

    results = {}
    for dim in dimensions:
        human_scores = []
        llm_scores = []

        for record in dataset:
            human_score = record.get("human_scores", {}).get(dim)
            llm_score = record.get("llm_scores", {}).get(dim)

            if human_score is not None and llm_score is not None:
                human_scores.append(float(human_score))
                llm_scores.append(float(llm_score))

        results[dim] = calculate_agreement_metrics(human_scores, llm_scores)

    # Calculate overall
    human_overalls = []
    llm_overalls = []
    for record in dataset:
        human_overall = record.get("human_scores", {}).get("overall")
        llm_overall = record.get("llm_scores", {}).get("overall")

        if human_overall is not None and llm_overall is not None:
            human_overalls.append(float(human_overall))
            llm_overalls.append(float(llm_overall))

    results["overall"] = calculate_agreement_metrics(human_overalls, llm_overalls)

    return results
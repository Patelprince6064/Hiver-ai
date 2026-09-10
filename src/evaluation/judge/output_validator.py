"""Output validator for LLM judge responses.

Validates that judge output conforms to the expected schema.
"""

from typing import Any

from src.evaluation.judge_schema import FAILURE_TAGS


def validate_judge_output(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate judge output data.

    Args:
        data: Parsed JSON data from LLM output.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check required fields
    required_fields = [
        "relevance",
        "groundedness",
        "correctness",
        "helpfulness",
        "completeness",
        "style",
    ]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        else:
            # Validate score range
            score = data[field]
            if not isinstance(score, (int, float)):
                errors.append(f"Field '{field}' must be numeric, got {type(score).__name__}")
            elif not (1 <= score <= 5):
                errors.append(f"Field '{field}' must be between 1 and 5, got {score}")

    # Check failure_tags
    if "failure_tags" in data:
        tags = data["failure_tags"]
        if not isinstance(tags, list):
            errors.append("failure_tags must be a list")
        else:
            for tag in tags:
                if tag not in FAILURE_TAGS:
                    errors.append(f"Invalid failure tag: {tag}")

    # Check short_rationale
    if "short_rationale" in data:
        rationale = data["short_rationale"]
        if not isinstance(rationale, str):
            errors.append("short_rationale must be a string")
        elif len(rationale) > 500:
            errors.append(f"short_rationale too long: {len(rationale)} > 500 chars")

    return len(errors) == 0, errors


def recalculate_overall(scores: dict[str, int]) -> float:
    """Recalculate overall score from dimension scores.

    Args:
        scores: Dictionary with dimension scores.

    Returns:
        Mean of the six dimension scores.
    """
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]

    valid_scores = []
    for dim in dimensions:
        if dim in scores and isinstance(scores[dim], (int, float)):
            if 1 <= scores[dim] <= 5:
                valid_scores.append(scores[dim])

    if not valid_scores:
        return 1.0

    return round(sum(valid_scores) / len(valid_scores), 2)
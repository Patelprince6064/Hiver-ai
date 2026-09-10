"""Failure Priority Scoring.

Simple transparent scoring framework for failure prioritization.
"""

from dataclasses import dataclass
from typing import Optional

from src.evaluation.failure_severity import SEVERITY_DEFINITIONS


@dataclass
class PriorityConfig:
    """Configuration for priority calculation."""
    severity_weights: dict = None
    frequency_weight: float = 1.0
    severity_weight: float = 1.0
    impact_weight: float = 1.0
    
    def __post_init__(self):
        if self.severity_weights is None:
            self.severity_weights = {
                "LOW": 1,
                "MEDIUM": 2,
                "HIGH": 4,
                "CRITICAL": 8,
            }


DEFAULT_CONFIG = PriorityConfig()


def calculate_priority_score(
    frequency: int,
    severity: str,
    impact_score: float = 1.0,
    config: Optional[PriorityConfig] = None,
) -> float:
    """Calculate failure priority score.
    
    Args:
        frequency: Number of occurrences.
        severity: Severity level string.
        impact_score: Impact score (0-1 scale).
        config: Priority configuration.
        
    Returns:
        Priority score (higher = more important).
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    severity_weight = config.severity_weights.get(severity, 1)
    
    priority = (
        frequency * config.frequency_weight
        + severity_weight * config.severity_weight
        + impact_score * config.impact_weight
    )
    
    return priority


def rank_failures(
    failures: list[dict],
    config: Optional[PriorityConfig] = None,
) -> list[dict]:
    """Rank failures by priority score.
    
    Args:
        failures: List of failure dictionaries.
        config: Priority configuration.
        
    Returns:
        Sorted list of failures with priority scores.
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    ranked = []
    for failure in failures:
        frequency = failure.get("count", 1)
        severity = failure.get("severity", "LOW")
        impact = failure.get("impact_score", 1.0)
        
        priority = calculate_priority_score(frequency, severity, impact, config)
        
        ranked.append({
            **failure,
            "priority_score": priority,
        })
    
    # Sort by priority score (descending)
    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return ranked


def select_top_n(
    ranked_failures: list[dict],
    n: int = 5,
) -> list[dict]:
    """Select top N failures by priority.
    
    Args:
        ranked_failures: Ranked failure list.
        n: Number to select.
        
    Returns:
        Top N failures.
    """
    return ranked_failures[:n]
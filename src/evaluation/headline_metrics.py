"""Headline Metrics and Honesty Evaluation.

Defines candidate headline metrics, calculation methods, confidence intervals,
and honest delta comparisons against baselines.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Optional


@dataclass
class HeadlineMetricRecord:
    """Structured representation of the project headline metric."""
    metric_name: str
    value: float
    unit: str
    evaluation_set: str
    sample_size: int
    definition: str
    formula: str
    baseline: str
    baseline_value: float
    delta: float
    relative_delta: Optional[float] = None
    confidence_interval: Optional[list[float]] = None
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching Phase 22 schema."""
        return {
            "metric_name": self.metric_name,
            "value": round(self.value, 4),
            "unit": self.unit,
            "evaluation_set": self.evaluation_set,
            "sample_size": self.sample_size,
            "definition": self.definition,
            "formula": self.formula,
            "baseline": self.baseline,
            "baseline_value": round(self.baseline_value, 4),
            "delta": round(self.delta, 4),
            "relative_delta": round(self.relative_delta, 4) if self.relative_delta is not None else None,
            "confidence_interval": [round(x, 4) for x in self.confidence_interval] if self.confidence_interval else None,
            "limitations": self.limitations,
        }


def calculate_mean_ci(
    mean: float,
    std: float,
    n: int,
    confidence: float = 0.95,
) -> Optional[list[float]]:
    """Calculate normal/t confidence interval for a continuous mean.
    
    Args:
        mean: Sample mean.
        std: Sample standard deviation.
        n: Sample size.
        confidence: Confidence level (default 0.95).
        
    Returns:
        [lower_bound, upper_bound] or None if sample size < 2.
    """
    if n < 2 or std < 0:
        return None
    # For 95% CI, z ~= 1.96
    z = 1.96 if confidence == 0.95 else 2.576
    margin = z * (std / math.sqrt(n))
    return [max(0.0, mean - margin), min(1.0, mean + margin)]


def calculate_proportion_ci(
    p: float,
    n: int,
    confidence: float = 0.95,
) -> Optional[list[float]]:
    """Calculate Wilson score interval for proportions.
    
    Args:
        p: Proportion (0.0 to 1.0).
        n: Sample size.
        confidence: Confidence level (default 0.95).
        
    Returns:
        [lower_bound, upper_bound] or None if n == 0.
    """
    if n <= 0:
        return None
    z = 1.96 if confidence == 0.95 else 2.576
    denominator = 1 + (z**2) / n
    centre_adjusted_probability = p + (z**2) / (2 * n)
    adjusted_std_dev = math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))
    lower_bound = (centre_adjusted_probability - z * adjusted_std_dev) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_std_dev) / denominator
    return [max(0.0, lower_bound), min(1.0, upper_bound)]


def calculate_deltas(value: float, baseline_value: float) -> tuple[float, Optional[float]]:
    """Calculate absolute and relative delta.
    
    Args:
        value: System metric value.
        baseline_value: Reference baseline metric value.
        
    Returns:
        (absolute_delta, relative_delta)
    """
    abs_delta = value - baseline_value
    if abs(baseline_value) < 1e-9:
        rel_delta = None
    else:
        rel_delta = (abs_delta / baseline_value) * 100.0
    return abs_delta, rel_delta


def get_candidate_metrics() -> dict[str, dict[str, Any]]:
    """Return catalog of candidate headline metrics evaluated in Phase 22."""
    return {
        "verified_reply_quality": {
            "name": "Mean Verified Reply Quality Score",
            "value": 0.767,
            "unit": "score (0.0 - 1.0)",
            "baseline": "Historical Response Baseline",
            "baseline_value": 0.500,
            "sample_size": 200,
            "relevance_score": 9,
            "interpretability_score": 9,
            "ground_truth_score": 7,
            "risk_of_misinterpretation": "Moderate",
            "selected": True,
            "rationale": "Directly evaluates customer-facing answer quality across 6 rubric dimensions.",
        },
        "intent_macro_f1": {
            "name": "Intent Classification Macro F1",
            "value": 0.857,
            "unit": "Macro F1",
            "baseline": "TF-IDF Baseline",
            "baseline_value": 0.580,
            "sample_size": 200,
            "relevance_score": 7,
            "interpretability_score": 8,
            "ground_truth_score": 9,
            "risk_of_misinterpretation": "High",
            "selected": False,
            "rationale": "Upstream metric only; does not evaluate whether customer inquiry was answered.",
        },
        "escalation_cost_reduction": {
            "name": "Escalation Expected Cost",
            "value": 2.14,
            "unit": "expected cost units",
            "baseline": "Always-Auto Baseline (Unsafe)",
            "baseline_value": 6.10,
            "sample_size": 200,
            "relevance_score": 8,
            "interpretability_score": 6,
            "ground_truth_score": 8,
            "risk_of_misinterpretation": "High",
            "selected": False,
            "rationale": "Cost model depends heavily on synthetic penalty assumptions (10x cost for missed escalation).",
        },
        "grounding_pass_rate": {
            "name": "Grounding Pass Rate",
            "value": 0.560,
            "unit": "rate (0.0 - 1.0)",
            "baseline": "Ungrounded LLM Pass Rate",
            "baseline_value": 0.350,
            "sample_size": 200,
            "relevance_score": 8,
            "interpretability_score": 7,
            "ground_truth_score": 7,
            "risk_of_misinterpretation": "High",
            "selected": False,
            "rationale": "Measures verifier string/embedding checks, not factual truth in external reality.",
        },
        "auto_handle_rate": {
            "name": "Auto-Handle Rate",
            "value": 0.700,
            "unit": "percentage",
            "baseline": "Always-Escalate (0.0%)",
            "baseline_value": 0.0,
            "sample_size": 200,
            "relevance_score": 7,
            "interpretability_score": 9,
            "ground_truth_score": 6,
            "risk_of_misinterpretation": "Critical",
            "selected": False,
            "rationale": "Highly misleading if reported alone; hides 2% unsafe auto-handle on high-risk requests.",
        },
    }

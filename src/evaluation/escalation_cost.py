"""Escalation cost analysis.

Defines configurable costs for false auto-handle and false escalation,
and computes expected policy cost for candidate policies.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EscalationCosts:
    """Configurable costs for escalation errors."""

    false_auto_handle_cost: float = 10.0
    false_escalation_cost: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return {
            "false_auto_handle_cost": self.false_auto_handle_cost,
            "false_escalation_cost": self.false_escalation_cost,
        }


@dataclass
class PolicyCostResult:
    """Result of cost analysis for a single policy."""

    policy_name: str
    policy_version: str
    false_auto_handle_rate: float
    false_escalation_rate: float
    expected_cost: float
    n_auto_handle: int = 0
    n_escalate: int = 0
    n_total: int = 0
    costs_used: EscalationCosts = field(default_factory=EscalationCosts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "false_auto_handle_rate": self.false_auto_handle_rate,
            "false_escalation_rate": self.false_escalation_rate,
            "expected_cost": self.expected_cost,
            "n_auto_handle": self.n_auto_handle,
            "n_escalate": self.n_escalate,
            "n_total": self.n_total,
            "costs_used": self.costs_used.to_dict(),
        }


def compute_expected_cost(
    false_auto_handle_rate: float,
    false_escalation_rate: float,
    costs: EscalationCosts | None = None,
) -> float:
    """Compute expected cost for a policy.

    Expected Cost = (False Auto-Handle Rate × Cost) +
                    (False Escalation Rate × Cost)

    Args:
        false_auto_handle_rate: Rate of false auto-handles (0.0 to 1.0).
        false_escalation_rate: Rate of false escalations (0.0 to 1.0).
        costs: Cost configuration.

    Returns:
        Expected cost value.
    """
    if costs is None:
        costs = EscalationCosts()

    return (
        false_auto_handle_rate * costs.false_auto_handle_cost +
        false_escalation_rate * costs.false_escalation_cost
    )


def analyze_policy_cost(
    policy_name: str,
    policy_version: str,
    predictions: list[str],
    gold_labels: list[str],
    costs: EscalationCosts | None = None,
) -> PolicyCostResult:
    """Analyze cost for a policy given predictions and gold labels.

    Args:
        policy_name: Name of the policy.
        policy_version: Version string.
        predictions: List of "AUTO_HANDLE" or "ESCALATE_TO_HUMAN".
        gold_labels: List of "AUTO_HANDLE" or "ESCALATE_TO_HUMAN".
        costs: Cost configuration.

    Returns:
        PolicyCostResult with cost analysis.
    """
    if costs is None:
        costs = EscalationCosts()

    if len(predictions) != len(gold_labels):
        raise ValueError("predictions and gold_labels must have the same length")

    n = len(predictions)
    if n == 0:
        return PolicyCostResult(
            policy_name=policy_name,
            policy_version=policy_version,
            false_auto_handle_rate=0.0,
            false_escalation_rate=0.0,
            expected_cost=0.0,
            costs_used=costs,
        )

    n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")
    n_true_auto = sum(1 for g in gold_labels if g == "AUTO_HANDLE")
    n_pred_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
    n_pred_escalate = sum(1 for p in predictions if p == "ESCALATE_TO_HUMAN")

    fn_escalate = 0  # False auto-handles
    fn_auto = 0  # False escalations

    for pred, gold in zip(predictions, gold_labels):
        if pred == "AUTO_HANDLE" and gold == "ESCALATE_TO_HUMAN":
            fn_escalate += 1
        elif pred == "ESCALATE_TO_HUMAN" and gold == "AUTO_HANDLE":
            fn_auto += 1

    false_auto_handle_rate = fn_escalate / n_true_escalate if n_true_escalate > 0 else 0.0
    false_escalation_rate = fn_auto / n_true_auto if n_true_auto > 0 else 0.0

    expected_cost = compute_expected_cost(
        false_auto_handle_rate, false_escalation_rate, costs
    )

    return PolicyCostResult(
        policy_name=policy_name,
        policy_version=policy_version,
        false_auto_handle_rate=false_auto_handle_rate,
        false_escalation_rate=false_escalation_rate,
        expected_cost=expected_cost,
        n_auto_handle=n_pred_auto,
        n_escalate=n_pred_escalate,
        n_total=n,
        costs_used=costs,
    )


def compare_policy_costs(
    policy_results: list[PolicyCostResult],
) -> list[PolicyCostResult]:
    """Sort policy cost results by expected cost (ascending).

    Args:
        policy_results: List of PolicyCostResult.

    Returns:
        Sorted list (lowest cost first).
    """
    return sorted(policy_results, key=lambda x: x.expected_cost)


def format_cost_comparison(results: list[PolicyCostResult]) -> str:
    """Format cost comparison as a readable table string."""
    lines = []
    lines.append(f"{'Policy':<25} {'Version':<10} {'FAH Rate':<10} {'FE Rate':<10} {'Cost':<10}")
    lines.append("-" * 65)
    for r in results:
        lines.append(
            f"{r.policy_name:<25} {r.policy_version:<10} "
            f"{r.false_auto_handle_rate:<10.4f} {r.false_escalation_rate:<10.4f} "
            f"{r.expected_cost:<10.4f}"
        )
    return "\n".join(lines)

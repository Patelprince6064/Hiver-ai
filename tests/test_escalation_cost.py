"""Tests for escalation_cost.py — Cost analysis module."""

import pytest
from src.evaluation.escalation_cost import (
    EscalationCosts,
    PolicyCostResult,
    analyze_policy_cost,
    compare_policy_costs,
    compute_expected_cost,
    format_cost_comparison,
)


class TestEscalationCosts:
    def test_default_costs(self):
        costs = EscalationCosts()
        assert costs.false_auto_handle_cost == 10.0
        assert costs.false_escalation_cost == 1.0

    def test_to_dict(self):
        costs = EscalationCosts(false_auto_handle_cost=5.0, false_escalation_cost=2.0)
        d = costs.to_dict()
        assert d["false_auto_handle_cost"] == 5.0
        assert d["false_escalation_cost"] == 2.0


class TestComputeExpectedCost:
    def test_zero_cost(self):
        cost = compute_expected_cost(0.0, 0.0)
        assert cost == 0.0

    def test_only_false_auto_handle(self):
        cost = compute_expected_cost(0.1, 0.0)
        assert cost == 1.0  # 0.1 * 10.0

    def test_only_false_escalation(self):
        cost = compute_expected_cost(0.0, 0.5)
        assert cost == 0.5  # 0.5 * 1.0

    def test_mixed_costs(self):
        cost = compute_expected_cost(0.05, 0.2)
        assert cost == 0.7  # 0.05*10 + 0.2*1 = 0.5 + 0.2

    def test_custom_costs(self):
        costs = EscalationCosts(false_auto_handle_cost=5.0, false_escalation_cost=3.0)
        cost = compute_expected_cost(0.1, 0.1, costs)
        assert cost == 0.8  # 0.1*5 + 0.1*3


class TestAnalyzePolicyCost:
    def test_perfect_predictions(self):
        predictions = ["AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        gold = ["AUTO_HANDLE", "AUTO_HANDLE", "ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]

        result = analyze_policy_cost("test", "v1", predictions, gold)
        assert result.expected_cost == 0.0
        assert result.false_auto_handle_rate == 0.0
        assert result.false_escalation_rate == 0.0

    def test_all_false_auto_handle(self):
        predictions = ["AUTO_HANDLE", "AUTO_HANDLE"]
        gold = ["ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]

        result = analyze_policy_cost("test", "v1", predictions, gold)
        assert result.false_auto_handle_rate == 1.0
        assert result.expected_cost == 10.0

    def test_all_false_escalation(self):
        predictions = ["ESCALATE_TO_HUMAN", "ESCALATE_TO_HUMAN"]
        gold = ["AUTO_HANDLE", "AUTO_HANDLE"]

        result = analyze_policy_cost("test", "v1", predictions, gold)
        assert result.false_escalation_rate == 1.0
        assert result.expected_cost == 1.0

    def test_empty_predictions(self):
        result = analyze_policy_cost("test", "v1", [], [])
        assert result.expected_cost == 0.0

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            analyze_policy_cost("test", "v1", ["AUTO_HANDLE"], ["A", "B"])


class TestComparePolicyCosts:
    def test_sort_by_cost(self):
        results = [
            PolicyCostResult("high_cost", "v1", 0.5, 0.0, 5.0),
            PolicyCostResult("low_cost", "v1", 0.0, 0.0, 0.0),
            PolicyCostResult("mid_cost", "v1", 0.1, 0.0, 1.0),
        ]
        sorted_results = compare_policy_costs(results)
        assert sorted_results[0].policy_name == "low_cost"
        assert sorted_results[2].policy_name == "high_cost"


class TestFormatCostComparison:
    def test_format(self):
        results = [
            PolicyCostResult("policy_a", "v1", 0.05, 0.1, 0.6),
            PolicyCostResult("policy_b", "v1", 0.1, 0.05, 1.05),
        ]
        formatted = format_cost_comparison(results)
        assert "policy_a" in formatted
        assert "policy_b" in formatted

#!/usr/bin/env python3
"""Compare escalation policies.

Usage:
    python scripts/compare_escalation_policies.py [--seed 42]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare escalation policies")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("ESCALATION POLICY COMPARISON")
    print("=" * 60)

    # Check for evaluation data
    eval_dir = PROJECT_ROOT / "data" / "interim" / "escalation_eval"
    if not eval_dir.exists():
        print(f"\nEvaluation data not found: {eval_dir}")
        print("Creating synthetic evaluation data for demonstration...")
        eval_data = _create_synthetic_eval_data()
    else:
        eval_file = eval_dir / "escalation_eval.jsonl"
        if not eval_file.exists():
            print(f"\nEvaluation file not found: {eval_file}")
            print("Creating synthetic evaluation data for demonstration...")
            eval_data = _create_synthetic_eval_data()
        else:
            with open(eval_file, "r") as f:
                eval_data = [json.loads(line) for line in f]

    print(f"\nLoaded {len(eval_data)} evaluation examples")

    # Extract signals and gold labels
    gold_labels = [item.get("gold_decision", "ESCALATE_TO_HUMAN") for item in eval_data]

    from src.escalation.baselines import AlwaysAutoHandle, AlwaysEscalate
    from src.escalation.rule_based_policy import RiskAwarePolicy, RuleBasedPolicy
    from src.escalation.risk_signals import extract_signals
    from src.evaluation.escalation_cost import EscalationCosts, analyze_policy_cost
    from src.evaluation.escalation_metrics import compute_escalation_metrics

    # Define policies
    policies = {
        "ALWAYS_AUTO_HANDLE": AlwaysAutoHandle(),
        "ALWAYS_ESCALATE": AlwaysEscalate(),
        "V1_0_CONSERVATIVE": RuleBasedPolicy(
            min_intent_confidence=0.70,
            policy_version="v1.0",
        ),
        "V1_1_RISK_AWARE": RiskAwarePolicy(
            min_intent_confidence=0.70,
            min_confidence_margin=0.15,
            policy_version="v1.1",
        ),
    }

    costs = EscalationCosts(false_auto_handle_cost=10.0, false_escalation_cost=1.0)

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_examples": len(eval_data),
        "costs": costs.to_dict(),
        "policies": {},
        "comparison": [],
    }

    print("\n" + "=" * 60)
    print("POLICY COMPARISON")
    print("=" * 60)

    for name, policy in policies.items():
        predictions = []

        for item in eval_data:
            signals = extract_signals(
                intent_result={
                    "intent": item.get("intent", ""),
                    "confidence": item.get("signals", {}).get("intent_confidence", 0.5),
                    "probabilities": {
                        item.get("intent", ""): item.get("signals", {}).get("intent_confidence", 0.5)
                    },
                },
                retrieval_result={
                    "retrieval_status": "success" if item.get("signals", {}).get("retrieval_quality_score", 0) > 0.3 else "no_evidence",
                    "results": [{"knowledge_id": "mock", "similarity_score": 0.5}] if item.get("signals", {}).get("retrieval_quality_score", 0) > 0.3 else [],
                },
                reply_result={
                    "status": "success",
                    "reply": "Mock reply",
                    "risk_flags": [],
                },
                grounding_result={
                    "status": item.get("signals", {}).get("grounding_status", "pass"),
                    "grounding_score": 0.8,
                    "risk_flags": [],
                    "unsupported_claims": [],
                    "repair_attempted": False,
                    "repair_succeeded": False,
                },
            )

            decision_obj = policy.evaluate(signals)
            # Handle both tuple returns (RuleBasedPolicy, RiskAwarePolicy) and EscalationDecision returns (baselines)
            if isinstance(decision_obj, tuple):
                decision = decision_obj[0]
            else:
                decision = decision_obj.decision
            predictions.append(decision)

        # Compute metrics
        metrics = compute_escalation_metrics(predictions, gold_labels)

        # Compute cost
        cost_result = analyze_policy_cost(
            policy_name=name,
            policy_version=policy.get_params().get("policy_version", "unknown"),
            predictions=predictions,
            gold_labels=gold_labels,
            costs=costs,
        )

        policy_result = {
            "policy_version": policy.get_params().get("policy_version", "unknown"),
            "accuracy": round(metrics.accuracy, 4),
            "auto_handle_rate": round(metrics.auto_handle_rate, 4),
            "escalate_rate": round(metrics.escalate_rate, 4),
            "false_auto_handle_rate": round(metrics.false_auto_handle_rate, 4),
            "false_escalation_rate": round(metrics.false_escalation_rate, 4),
            "auto_precision": round(metrics.auto_precision, 4),
            "auto_recall": round(metrics.auto_recall, 4),
            "auto_f1": round(metrics.auto_f1, 4),
            "escalate_precision": round(metrics.escalate_precision, 4),
            "escalate_recall": round(metrics.escalate_recall, 4),
            "escalate_f1": round(metrics.escalate_f1, 4),
            "expected_cost": round(cost_result.expected_cost, 4),
        }

        results["policies"][name] = policy_result
        results["comparison"].append({
            "policy_name": name,
            **policy_result,
        })

        print(f"\n{name} ({policy_result['policy_version']}):")
        print(f"  Accuracy:              {policy_result['accuracy']:.4f}")
        print(f"  Auto-handle rate:      {policy_result['auto_handle_rate']:.4f}")
        print(f"  Escalate rate:         {policy_result['escalate_rate']:.4f}")
        print(f"  False auto-handle:     {policy_result['false_auto_handle_rate']:.4f}")
        print(f"  False escalation:      {policy_result['false_escalation_rate']:.4f}")
        print(f"  Expected cost:         {policy_result['expected_cost']:.4f}")

    # Save results
    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "escalation_policy_comparison.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)

    # Sort by expected cost
    sorted_policies = sorted(
        results["comparison"],
        key=lambda x: x["expected_cost"],
    )

    print(f"\n{'Policy':<25} {'Version':<10} {'Auto Rate':<12} {'FAH Rate':<12} {'Cost':<10}")
    print("-" * 69)
    for p in sorted_policies:
        print(
            f"{p['policy_name']:<25} {p['policy_version']:<10} "
            f"{p['auto_handle_rate']:<12.4f} {p['false_auto_handle_rate']:<12.4f} "
            f"{p['expected_cost']:<10.4f}"
        )

    print(f"\nResults saved to: {output_path}")
    return 0


def _create_synthetic_eval_data() -> list[dict]:
    """Create synthetic evaluation data for demonstration."""
    import random

    random.seed(42)
    data = []

    intents = [
        "order_status", "billing_issue", "refund_request", "product_question",
        "technical_support", "account_help", "shipping_info", "complaint",
    ]

    for i in range(100):
        intent = random.choice(intents)
        confidence = random.uniform(0.3, 0.95)
        margin = random.uniform(0.05, 0.5)

        is_high_risk = intent in ("billing_issue", "refund_request", "account_help")
        has_low_confidence = confidence < 0.6

        gold_decision = "ESCALATE_TO_HUMAN" if (is_high_risk or has_low_confidence) else "AUTO_HANDLE"

        data.append({
            "query_id": f"q_{i:04d}",
            "customer_message": f"Sample message about {intent}",
            "intent": intent,
            "gold_decision": gold_decision,
            "signals": {
                "intent_confidence": confidence,
                "confidence_margin": margin,
                "retrieval_quality_score": random.uniform(0.3, 0.9),
                "grounding_status": "pass" if random.random() > 0.2 else "fail",
            },
        })

    return data


if __name__ == "__main__":
    sys.exit(main())

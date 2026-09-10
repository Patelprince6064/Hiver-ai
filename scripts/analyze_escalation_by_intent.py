#!/usr/bin/env python3
"""Analyze escalation patterns by intent.

Usage:
    python scripts/analyze_escalation_by_intent.py [--seed 42]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze escalation by intent")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("ESCALATION BY INTENT ANALYSIS")
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

    # Run policy on each example
    from src.escalation.rule_based_policy import RuleBasedPolicy
    from src.escalation.risk_signals import extract_signals

    policy = RuleBasedPolicy(min_intent_confidence=0.70, policy_version="v1.0")

    # Aggregate by intent
    intent_stats: dict[str, dict] = {}

    for item in eval_data:
        intent = item.get("intent", "unknown")
        gold_decision = item.get("gold_decision", "ESCALATE_TO_HUMAN")

        signals = extract_signals(
            intent_result={
                "intent": intent,
                "confidence": item.get("signals", {}).get("intent_confidence", 0.5),
                "probabilities": {
                    intent: item.get("signals", {}).get("intent_confidence", 0.5)
                },
            },
            retrieval_result={
                "retrieval_status": "success",
                "results": [{"knowledge_id": "mock", "similarity_score": 0.5}],
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

        decision, reason_codes = policy.evaluate(signals)

        if intent not in intent_stats:
            intent_stats[intent] = {
                "total": 0,
                "auto_handle": 0,
                "escalate": 0,
                "true_auto": 0,
                "true_escalate": 0,
                "correct_auto": 0,
                "correct_escalate": 0,
                "false_auto": 0,
                "false_escalate": 0,
            }

        stats = intent_stats[intent]
        stats["total"] += 1

        if decision == "AUTO_HANDLE":
            stats["auto_handle"] += 1
        else:
            stats["escalate"] += 1

        if gold_decision == "AUTO_HANDLE":
            stats["true_auto"] += 1
            if decision == "AUTO_HANDLE":
                stats["correct_auto"] += 1
            else:
                stats["false_escalate"] += 1
        else:
            stats["true_escalate"] += 1
            if decision == "ESCALATE_TO_HUMAN":
                stats["correct_escalate"] += 1
            else:
                stats["false_auto"] += 1

    # Compute metrics per intent
    results = {
        "per_intent": {},
        "top_escalation_rate": [],
        "top_false_auto_rate": [],
    }

    print(f"\n{'Intent':<25} {'Total':<8} {'Auto%':<10} {'Esc%':<10} {'FAH Rate':<12}")
    print("-" * 65)

    for intent, stats in sorted(intent_stats.items()):
        auto_rate = stats["auto_handle"] / stats["total"] if stats["total"] > 0 else 0
        escalate_rate = stats["escalate"] / stats["total"] if stats["total"] > 0 else 0
        fah_rate = stats["false_auto"] / stats["true_escalate"] if stats["true_escalate"] > 0 else 0
        false_esc_rate = stats["false_escalate"] / stats["true_auto"] if stats["true_auto"] > 0 else 0

        intent_result = {
            "total": stats["total"],
            "auto_handle_rate": round(auto_rate, 4),
            "escalate_rate": round(escalate_rate, 4),
            "false_auto_handle_rate": round(fah_rate, 4),
            "false_escalation_rate": round(false_esc_rate, 4),
            "true_auto": stats["true_auto"],
            "true_escalate": stats["true_escalate"],
        }

        results["per_intent"][intent] = intent_result

        print(f"{intent:<25} {stats['total']:<8} {auto_rate:<10.4f} {escalate_rate:<10.4f} {fah_rate:<12.4f}")

    # Find top escalation rate intents
    sorted_by_escalation = sorted(
        results["per_intent"].items(),
        key=lambda x: x[1]["escalate_rate"],
        reverse=True,
    )

    results["top_escalation_rate"] = [
        {"intent": intent, "escalate_rate": data["escalate_rate"]}
        for intent, data in sorted_by_escalation[:5]
    ]

    # Find top false auto-handle rate intents
    intents_with_fah = [
        (intent, data)
        for intent, data in results["per_intent"].items()
        if data["true_escalate"] > 0
    ]
    sorted_by_fah = sorted(
        intents_with_fah,
        key=lambda x: x[1]["false_auto_handle_rate"],
        reverse=True,
    )

    results["top_false_auto_rate"] = [
        {"intent": intent, "false_auto_handle_rate": data["false_auto_handle_rate"]}
        for intent, data in sorted_by_fah[:5]
    ]

    print(f"\n{'=' * 60}")
    print("TOP 5 ESCALATION RATE INTENTS")
    print("=" * 60)
    for item in results["top_escalation_rate"]:
        print(f"  {item['intent']:<25} {item['escalate_rate']:.4f}")

    print(f"\n{'=' * 60}")
    print("TOP 5 FALSE AUTO-HANDLE RATE INTENTS")
    print("=" * 60)
    for item in results["top_false_auto_rate"]:
        print(f"  {item['intent']:<25} {item['false_auto_handle_rate']:.4f}")

    # Save results
    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "escalation_by_intent.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

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

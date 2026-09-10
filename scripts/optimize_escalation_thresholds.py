#!/usr/bin/env python3
"""Optimize escalation thresholds on DEV data.

Usage:
    python scripts/optimize_escalation_thresholds.py [--seed 42]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize escalation thresholds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("ESCALATION THRESHOLD OPTIMIZATION")
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
    confidence_scores = []
    gold_labels = []
    confidence_margins = []
    retrieval_quality_scores = []

    for item in eval_data:
        signals = item.get("signals", {})
        confidence = signals.get("intent_confidence", 0.5)
        confidence_scores.append(confidence)
        gold_labels.append(item.get("gold_decision", "ESCALATE_TO_HUMAN"))
        confidence_margins.append(signals.get("confidence_margin", 0.5))
        retrieval_quality_scores.append(signals.get("retrieval_quality_score", 0.5))

    # Intent confidence thresholds
    intent_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

    # Margin thresholds
    margin_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_examples": len(eval_data),
        "intent_threshold_analysis": [],
        "margin_threshold_analysis": [],
        "combined_analysis": [],
    }

    # Analyze intent confidence thresholds
    print("\n" + "=" * 60)
    print("INTENT CONFIDENCE THRESHOLD ANALYSIS")
    print("=" * 60)
    print(f"{'Threshold':<12} {'Auto Rate':<12} {'FAH Rate':<12} {'N Auto':<10} {'N FAH':<10}")
    print("-" * 56)

    for threshold in intent_thresholds:
        predictions = []
        for score in confidence_scores:
            if score >= threshold:
                predictions.append("AUTO_HANDLE")
            else:
                predictions.append("ESCALATE_TO_HUMAN")

        n_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
        n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")
        fn_escalate = sum(
            1 for p, g in zip(predictions, gold_labels)
            if p == "AUTO_HANDLE" and g == "ESCALATE_TO_HUMAN"
        )

        auto_rate = n_auto / len(predictions) if predictions else 0
        fah_rate = fn_escalate / n_true_escalate if n_true_escalate > 0 else 0

        results["intent_threshold_analysis"].append({
            "threshold": threshold,
            "auto_handle_rate": round(auto_rate, 4),
            "false_auto_handle_rate": round(fah_rate, 4),
            "n_auto_handle": n_auto,
            "n_false_auto": fn_escalate,
        })

        print(f"{threshold:<12.2f} {auto_rate:<12.4f} {fah_rate:<12.4f} {n_auto:<10} {fn_escalate:<10}")

    # Analyze margin thresholds
    print("\n" + "=" * 60)
    print("CONFIDENCE MARGIN THRESHOLD ANALYSIS")
    print("=" * 60)
    print(f"{'Threshold':<12} {'Auto Rate':<12} {'FAH Rate':<12} {'N Auto':<10} {'N FAH':<10}")
    print("-" * 56)

    for threshold in margin_thresholds:
        predictions = []
        for margin, confidence in zip(confidence_margins, confidence_scores):
            # Escalate if margin is below threshold AND confidence is not very high
            if margin < threshold and confidence < 0.85:
                predictions.append("ESCALATE_TO_HUMAN")
            else:
                predictions.append("AUTO_HANDLE")

        n_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
        n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")
        fn_escalate = sum(
            1 for p, g in zip(predictions, gold_labels)
            if p == "AUTO_HANDLE" and g == "ESCALATE_TO_HUMAN"
        )

        auto_rate = n_auto / len(predictions) if predictions else 0
        fah_rate = fn_escalate / n_true_escalate if n_true_escalate > 0 else 0

        results["margin_threshold_analysis"].append({
            "threshold": threshold,
            "auto_handle_rate": round(auto_rate, 4),
            "false_auto_handle_rate": round(fah_rate, 4),
            "n_auto_handle": n_auto,
            "n_false_auto": fn_escalate,
        })

        print(f"{threshold:<12.2f} {auto_rate:<12.4f} {fah_rate:<12.4f} {n_auto:<10} {fn_escalate:<10}")

    # Combined analysis: intent threshold + margin threshold
    print("\n" + "=" * 60)
    print("COMBINED ANALYSIS (Intent + Margin)")
    print("=" * 60)
    print(f"{'Intent':<10} {'Margin':<10} {'Auto Rate':<12} {'FAH Rate':<12}")
    print("-" * 44)

    best_fah_rate = 1.0
    best_auto_rate = 0.0
    best_config = {}

    for intent_t in [0.65, 0.70, 0.75, 0.80]:
        for margin_t in [0.10, 0.15, 0.20]:
            predictions = []
            for conf, margin in zip(confidence_scores, confidence_margins):
                if conf < intent_t:
                    predictions.append("ESCALATE_TO_HUMAN")
                elif margin < margin_t and conf < 0.85:
                    predictions.append("ESCALATE_TO_HUMAN")
                else:
                    predictions.append("AUTO_HANDLE")

            n_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
            n_true_escalate = sum(1 for g in gold_labels if g == "ESCALATE_TO_HUMAN")
            fn_escalate = sum(
                1 for p, g in zip(predictions, gold_labels)
                if p == "AUTO_HANDLE" and g == "ESCALATE_TO_HUMAN"
            )

            auto_rate = n_auto / len(predictions) if predictions else 0
            fah_rate = fn_escalate / n_true_escalate if n_true_escalate > 0 else 0

            results["combined_analysis"].append({
                "intent_threshold": intent_t,
                "margin_threshold": margin_t,
                "auto_handle_rate": round(auto_rate, 4),
                "false_auto_handle_rate": round(fah_rate, 4),
                "n_auto_handle": n_auto,
                "n_false_auto": fn_escalate,
            })

            # Track best config with low FAH rate and reasonable auto rate
            if fah_rate <= 0.05 and auto_rate > best_auto_rate:
                best_fah_rate = fah_rate
                best_auto_rate = auto_rate
                best_config = {
                    "intent_threshold": intent_t,
                    "margin_threshold": margin_t,
                    "auto_handle_rate": round(auto_rate, 4),
                    "false_auto_handle_rate": round(fah_rate, 4),
                }

            print(f"{intent_t:<10.2f} {margin_t:<10.2f} {auto_rate:<12.4f} {fah_rate:<12.4f}")

    results["recommended_config"] = best_config

    # Save results
    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "escalation_threshold_optimization.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}")
    print("RECOMMENDED CONFIGURATION")
    print("=" * 60)
    if best_config:
        print(f"Intent threshold: {best_config.get('intent_threshold', 'N/A')}")
        print(f"Margin threshold: {best_config.get('margin_threshold', 'N/A')}")
        print(f"Auto-handle rate: {best_config.get('auto_handle_rate', 'N/A')}")
        print(f"False auto-handle rate: {best_config.get('false_auto_handle_rate', 'N/A')}")
    else:
        print("No configuration met the safety constraint (FAH rate <= 5%)")

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

        # Determine gold decision based on risk signals
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

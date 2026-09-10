#!/usr/bin/env python3
"""Analyze policy stability under threshold changes.

Usage:
    python scripts/analyze_policy_stability.py [--seed 42]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze policy stability")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("POLICY STABILITY ANALYSIS")
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

    # Extract confidence scores
    confidence_scores = [
        item.get("signals", {}).get("intent_confidence", 0.5)
        for item in eval_data
    ]

    # Test threshold stability
    base_threshold = 0.70
    perturbations = [-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02]

    results = {
        "base_threshold": base_threshold,
        "perturbations": perturbations,
        "stability_analysis": [],
        "summary": {},
    }

    print(f"\nBase threshold: {base_threshold}")
    print("\nTesting small perturbations...")
    print(f"{'Perturbation':<15} {'Threshold':<12} {'Auto Rate':<12} {'Changed':<10} {'% Changed':<12}")
    print("-" * 61)

    base_predictions = _predict_at_threshold(confidence_scores, base_threshold)
    base_auto_rate = sum(1 for p in base_predictions if p == "AUTO_HANDLE") / len(base_predictions)

    total_changed = 0
    total_auto_to_escalate = 0
    total_escalate_to_auto = 0

    for perturbation in perturbations:
        threshold = base_threshold + perturbation
        predictions = _predict_at_threshold(confidence_scores, threshold)

        # Count changes
        changed = 0
        auto_to_escalate = 0
        escalate_to_auto = 0

        for base_pred, new_pred in zip(base_predictions, predictions):
            if base_pred != new_pred:
                changed += 1
                if base_pred == "AUTO_HANDLE" and new_pred == "ESCALATE_TO_HUMAN":
                    auto_to_escalate += 1
                elif base_pred == "ESCALATE_TO_HUMAN" and new_pred == "AUTO_HANDLE":
                    escalate_to_auto += 1

        n_auto = sum(1 for p in predictions if p == "AUTO_HANDLE")
        auto_rate = n_auto / len(predictions)
        pct_changed = changed / len(predictions) * 100

        results["stability_analysis"].append({
            "perturbation": perturbation,
            "threshold": round(threshold, 4),
            "auto_handle_rate": round(auto_rate, 4),
            "n_changed": changed,
            "pct_changed": round(pct_changed, 2),
            "auto_to_escalate": auto_to_escalate,
            "escalate_to_auto": escalate_to_auto,
        })

        total_changed += changed
        total_auto_to_escalate += auto_to_escalate
        total_escalate_to_auto += escalate_to_auto

        print(f"{perturbation:<+15.3f} {threshold:<12.4f} {auto_rate:<12.4f} {changed:<10} {pct_changed:<12.2f}")

    # Compute stability metrics
    avg_changed = total_changed / len(perturbations) if perturbations else 0
    avg_pct_changed = avg_changed / len(confidence_scores) * 100

    results["summary"] = {
        "avg_changes_per_perturbation": round(avg_changed, 2),
        "avg_pct_changed": round(avg_pct_changed, 2),
        "total_auto_to_escalate": total_auto_to_escalate,
        "total_escalate_to_auto": total_escalate_to_auto,
        "stability_assessment": _assess_stability(avg_pct_changed),
    }

    print(f"\n{'=' * 60}")
    print("STABILITY ASSESSMENT")
    print("=" * 60)
    print(f"Average changes per perturbation: {avg_changed:.2f}")
    print(f"Average % changed: {avg_pct_changed:.2f}%")
    print(f"Auto->Escalate changes: {total_auto_to_escalate}")
    print(f"Escalate->Auto changes: {total_escalate_to_auto}")
    print(f"Stability: {results['summary']['stability_assessment']}")

    # Save results
    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "escalation_policy_stability.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    return 0


def _predict_at_threshold(
    confidence_scores: list[float],
    threshold: float,
) -> list[str]:
    """Make predictions based on confidence threshold."""
    predictions = []
    for score in confidence_scores:
        if score >= threshold:
            predictions.append("AUTO_HANDLE")
        else:
            predictions.append("ESCALATE_TO_HUMAN")
    return predictions


def _assess_stability(avg_pct_changed: float) -> str:
    """Assess policy stability based on average percentage changed."""
    if avg_pct_changed < 1.0:
        return "STABLE (very small changes)"
    elif avg_pct_changed < 5.0:
        return "MODERATE (small but noticeable changes)"
    elif avg_pct_changed < 10.0:
        return "UNSTABLE (significant changes)"
    else:
        return "VERY UNSTABLE (large changes with small perturbations)"


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

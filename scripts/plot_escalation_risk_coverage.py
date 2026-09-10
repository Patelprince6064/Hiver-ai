#!/usr/bin/env python3
"""Plot escalation risk-coverage curve.

Usage:
    python scripts/plot_escalation_risk_coverage.py [--seed 42]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot escalation risk-coverage curve")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("ESCALATION RISK-COVERAGE CURVE")
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
    confidence_scores = [
        item.get("signals", {}).get("intent_confidence", 0.5)
        for item in eval_data
    ]
    gold_labels = [item.get("gold_decision", "ESCALATE_TO_HUMAN") for item in eval_data]

    # Generate threshold variants
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

    threshold_points = []
    for threshold in thresholds:
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

        threshold_points.append({
            "threshold": threshold,
            "auto_handle_rate": round(auto_rate, 4),
            "false_auto_handle_rate": round(fah_rate, 4),
        })

    # Fixed policy points
    policy_points = {
        "Always Auto": {"auto_handle_rate": 1.0, "false_auto_handle_rate": 1.0},
        "Always Escalate": {"auto_handle_rate": 0.0, "false_auto_handle_rate": 0.0},
        "v1.0 (0.70)": {"auto_handle_rate": 0.4, "false_auto_handle_rate": 0.03},
        "v1.1 (0.70+0.15)": {"auto_handle_rate": 0.45, "false_auto_handle_rate": 0.02},
    }

    # Try to plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        # Plot threshold curve
        x_thresholds = [p["auto_handle_rate"] for p in threshold_points]
        y_thresholds = [p["false_auto_handle_rate"] for p in threshold_points]
        ax.plot(x_thresholds, y_thresholds, "b-o", label="Intent Threshold Variants", linewidth=2)

        # Plot fixed policy points
        colors = {"Always Auto": "red", "Always Escalate": "green", "v1.0 (0.70)": "orange", "v1.1 (0.70+0.15)": "purple"}
        for name, point in policy_points.items():
            ax.scatter(
                point["auto_handle_rate"],
                point["false_auto_handle_rate"],
                c=colors.get(name, "gray"),
                s=100,
                label=name,
                zorder=5,
            )

        ax.set_xlabel("Auto-Handle Rate (Coverage)", fontsize=12)
        ax.set_ylabel("False Auto-Handle Rate (Safety Risk)", fontsize=12)
        ax.set_title("Escalation Risk-Coverage Curve", fontsize=14)
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)

        # Add annotations
        for point in threshold_points:
            ax.annotate(
                f"{point['threshold']:.2f}",
                (point["auto_handle_rate"], point["false_auto_handle_rate"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
            )

        output_dir = PROJECT_ROOT / "evaluation" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "escalation_risk_coverage.png"

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"\nPlot saved to: {output_path}")

    except ImportError:
        print("\nmatplotlib not available. Skipping plot generation.")
        print("Install with: pip install matplotlib")

    # Save data
    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "escalation_risk_coverage_data.json"

    with open(data_path, "w") as f:
        json.dump({
            "threshold_points": threshold_points,
            "policy_points": policy_points,
        }, f, indent=2)

    print(f"Data saved to: {data_path}")

    # Print table
    print(f"\n{'Threshold':<12} {'Auto Rate':<12} {'FAH Rate':<12}")
    print("-" * 36)
    for point in threshold_points:
        print(f"{point['threshold']:<12.2f} {point['auto_handle_rate']:<12.4f} {point['false_auto_handle_rate']:<12.4f}")

    print(f"\n{'=' * 60}")
    print("FIXED POLICY POINTS")
    print("=" * 60)
    for name, point in policy_points.items():
        print(f"{name:<25} Auto: {point['auto_handle_rate']:.4f}  FAH: {point['false_auto_handle_rate']:.4f}")

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

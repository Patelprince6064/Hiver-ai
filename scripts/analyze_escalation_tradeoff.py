#!/usr/bin/env python3
"""Analyze escalation threshold tradeoff.

Usage:
    python scripts/analyze_escalation_tradeoff.py
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze escalation threshold tradeoff")
    parser.add_argument("--split", default="dev", help="Data split")
    args = parser.parse_args()

    config_path = PROJECT_ROOT / "configs" / "escalation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    output_dir = PROJECT_ROOT / config["escalation"]["eval"]["results_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "escalation_results.json"
    if not results_path.exists():
        print(f"Error: {results_path} not found.")
        print("Run: python scripts/evaluate_escalation.py first.")
        return 1

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    print("=" * 60)
    print("ESCALATION THRESHOLD TRADEOFF ANALYSIS")
    print("=" * 60)
    print(f"\nResults loaded: {len(results)} decisions")

    confidence_scores = [r["confidence"] for r in results]
    gold_labels = ["AUTO_HANDLE"] * len(results)

    from src.evaluation.escalation_metrics import compute_threshold_analysis

    analysis = compute_threshold_analysis(
        confidence_scores=confidence_scores,
        gold_labels=gold_labels,
    )

    print(f"\n--- Threshold Analysis ---")
    print(f"{'Threshold':>10} {'Auto-Handle%':>14} {'False-Auto%':>13} {'N-Auto':>8}")
    for row in analysis:
        print(f"{row['threshold']:>10.2f} {row['auto_handle_rate']:>13.1%} {row['false_auto_handle_rate']:>12.1%} {row['n_auto_handle']:>8}")

    analysis_path = output_dir / "escalation_threshold_analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nSaved: {analysis_path}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        thresholds = [a["threshold"] for a in analysis]
        auto_rates = [a["auto_handle_rate"] for a in analysis]
        false_rates = [a["false_auto_handle_rate"] for a in analysis]

        fig, ax1 = plt.subplots(figsize=(10, 6))

        color1 = "#2196F3"
        color2 = "#F44336"

        ax1.set_xlabel("Confidence Threshold")
        ax1.set_ylabel("Auto-Handle Rate", color=color1)
        ax1.plot(thresholds, auto_rates, marker="o", color=color1, label="Auto-Handle Rate")
        ax1.tick_params(axis="y", labelcolor=color1)

        ax2 = ax1.twinx()
        ax2.set_ylabel("False Auto-Handle Rate", color=color2)
        ax2.plot(thresholds, false_rates, marker="s", color=color2, label="False Auto-Handle Rate")
        ax2.tick_params(axis="y", labelcolor=color2)

        plt.title("Escalation Threshold Tradeoff\n(Auto-Handle Rate vs False Auto-Handle Rate)")
        fig.tight_layout()

        plot_path = output_dir / "escalation_tradeoff.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Plot: {plot_path}")
    except ImportError:
        print("matplotlib not available — skipping plot generation.")

    print(f"\n{'=' * 60}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

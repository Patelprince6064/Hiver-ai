#!/usr/bin/env python3
"""Analyze copying risks in historical baseline replies.

Usage:
    python scripts/analyze_reply_copy_risk.py [--input evaluation/results/historical_reply_predictions.jsonl]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generation.safety_filters import analyze_reply_safety


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze reply copying risks")
    parser.add_argument(
        "--input",
        default="evaluation/results/historical_reply_predictions.jsonl",
        help="Path to historical predictions JSONL",
    )
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    if not input_path.exists():
        print(f"Error: {input_path} not found.\nRun: python scripts/evaluate_reply_baselines.py")
        return 1

    print("=" * 60)
    print("REPLY COPYING RISK ANALYSIS")
    print("=" * 60)

    predictions = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                predictions.append(json.loads(line))

    print(f"\nTotal predictions: {len(predictions)}")

    all_risk_flags = []
    replies_with_risk = 0
    replies_with_pii = 0
    replies_with_url = 0
    replies_with_identifier = 0

    risk_details = []

    for pred in predictions:
        reply = pred.get("reply")
        if not reply:
            continue

        safety = analyze_reply_safety(reply)
        if safety.has_risk:
            replies_with_risk += 1
            all_risk_flags.extend(safety.flags)

            if any(f in safety.flags for f in ["contains_email", "contains_phone_number"]):
                replies_with_pii += 1
            if "contains_url" in safety.flags:
                replies_with_url += 1
            if any(f in safety.flags for f in ["contains_order_id", "contains_ticket_reference"]):
                replies_with_identifier += 1

            risk_details.append({
                "query": pred.get("query", "")[:100],
                "reply": reply[:200],
                "risk_flags": safety.flags,
            })

    total_with_reply = sum(1 for p in predictions if p.get("reply"))

    print(f"\nReplies with risk flags: {replies_with_risk}/{total_with_reply} ({replies_with_risk/total_with_reply:.1%})" if total_with_reply else "\nNo replies to analyze")
    print(f"PII detected: {replies_with_pii}/{total_with_reply}")
    print(f"URLs detected: {replies_with_url}/{total_with_reply}")
    print(f"Identifiers detected: {replies_with_identifier}/{total_with_reply}")

    print(f"\nFlag distribution:")
    flag_counts = Counter(all_risk_flags)
    for flag, count in flag_counts.most_common():
        print(f"  {flag}: {count}")

    # Save results
    output_path = PROJECT_ROOT / "evaluation" / "results" / "reply_copy_risk_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_predictions": len(predictions),
            "total_with_reply": total_with_reply,
            "replies_with_risk": replies_with_risk,
            "risk_rate": replies_with_risk / total_with_reply if total_with_reply else 0,
            "pii_count": replies_with_pii,
            "url_count": replies_with_url,
            "identifier_count": replies_with_identifier,
            "flag_distribution": dict(flag_counts),
            "sample_risks": risk_details[:20],
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    print(f"\n{'=' * 60}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

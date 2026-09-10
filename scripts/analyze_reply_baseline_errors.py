#!/usr/bin/env python3
"""Analyze reply baseline errors and failure categories.

Usage:
    python scripts/analyze_reply_baseline_errors.py \
        --generic evaluation/results/generic_reply_predictions.jsonl \
        --historical evaluation/results/historical_reply_predictions.jsonl
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generation.safety_filters import analyze_reply_safety


FAILURE_CATEGORIES = {
    1: "Correct historical response",
    2: "Relevant issue but wrong resolution",
    3: "Semantically similar but contextually wrong",
    4: "Customer-specific information copied",
    5: "Incomplete response",
    6: "Outdated/uncertain historical behavior",
    7: "No useful historical evidence",
    8: "Generic response is safer than historical response",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze reply baseline errors")
    parser.add_argument("--generic", default="evaluation/results/generic_reply_predictions.jsonl")
    parser.add_argument("--historical", default="evaluation/results/historical_reply_predictions.jsonl")
    args = parser.parse_args()

    generic_path = PROJECT_ROOT / args.generic
    historical_path = PROJECT_ROOT / args.historical

    if not generic_path.exists():
        print(f"Error: {generic_path} not found.\nRun: python scripts/evaluate_reply_baselines.py")
        return 1
    if not historical_path.exists():
        print(f"Error: {historical_path} not found.\nRun: python scripts/evaluate_reply_baselines.py")
        return 1

    print("=" * 60)
    print("REPLY BASELINE ERROR ANALYSIS")
    print("=" * 60)

    # Load predictions
    generic_preds = []
    with open(generic_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                generic_preds.append(json.loads(line))

    historical_preds = []
    with open(historical_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                historical_preds.append(json.loads(line))

    print(f"\nGeneric predictions: {len(generic_preds)}")
    print(f"Historical predictions: {len(historical_preds)}")

    # Categorize failures
    insufficient_evidence = 0
    safety_risk_replies = 0
    identical_to_generic = 0
    short_replies = 0
    long_replies = 0
    category_counts = Counter()

    for pred in historical_preds:
        status = pred.get("status")
        reply = pred.get("reply")
        risk_flags = pred.get("risk_flags", [])

        if status == "insufficient_evidence":
            insufficient_evidence += 1
            category_counts[7] += 1
            continue

        if not reply:
            category_counts[7] += 1
            continue

        if risk_flags:
            safety_risk_replies += 1
            if any(f in risk_flags for f in ["contains_order_id", "contains_email", "contains_phone_number"]):
                category_counts[4] += 1

        if len(reply.split()) < 5:
            short_replies += 1
            category_counts[5] += 1
        elif len(reply.split()) > 100:
            long_replies += 1
            category_counts[6] += 1

    # Check for identical generic fallbacks
    generic_reply_text = None
    for pred in generic_preds:
        if pred.get("reply"):
            generic_reply_text = pred["reply"]
            break

    if generic_reply_text:
        for pred in historical_preds:
            if pred.get("reply") == generic_reply_text:
                identical_to_generic += 1
                category_counts[8] += 1

    # Summary
    print(f"\n--- Historical Baseline Summary ---")
    print(f"Insufficient evidence: {insufficient_evidence}/{len(historical_preds)}")
    print(f"Safety-risk replies: {safety_risk_replies}/{len(historical_preds)}")
    print(f"Identical to generic: {identical_to_generic}/{len(historical_preds)}")
    print(f"Short replies (<5 words): {short_replies}/{len(historical_preds)}")
    print(f"Long replies (>100 words): {long_replies}/{len(historical_preds)}")

    print(f"\n--- Failure Categories ---")
    for cat_id, count in category_counts.most_common():
        print(f"  Category {cat_id} ({FAILURE_CATEGORIES[cat_id]}): {count}")

    # Sample problematic replies
    print(f"\n--- Sample Safety-Risk Replies ---")
    shown = 0
    for pred in historical_preds:
        if pred.get("risk_flags") and shown < 5:
            print(f"\n  Query: {pred.get('query', '')[:80]}...")
            print(f"  Reply: {pred.get('reply', '')[:120]}...")
            print(f"  Flags: {pred.get('risk_flags', [])}")
            shown += 1

    print(f"\n--- Sample Insufficient Evidence ---")
    shown = 0
    for pred in historical_preds:
        if pred.get("status") == "insufficient_evidence" and shown < 5:
            print(f"\n  Query: {pred.get('query', '')[:80]}...")
            print(f"  Intent: {pred.get('predicted_intent')}")
            shown += 1

    # Save results
    output_path = PROJECT_ROOT / "evaluation" / "results" / "reply_error_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_generic": len(generic_preds),
            "total_historical": len(historical_preds),
            "insufficient_evidence": insufficient_evidence,
            "safety_risk_replies": safety_risk_replies,
            "identical_to_generic": identical_to_generic,
            "short_replies": short_replies,
            "long_replies": long_replies,
            "failure_categories": dict(category_counts),
            "category_descriptions": FAILURE_CATEGORIES,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    print(f"\n{'=' * 60}")
    print("ERROR ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

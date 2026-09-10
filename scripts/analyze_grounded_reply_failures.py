#!/usr/bin/env python3
"""Analyze failures in grounded reply generation.

Usage:
    python scripts/analyze_grounded_reply_failures.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


FAILURE_CATEGORIES = {
    1: "LLM hallucinates unsupported information",
    2: "LLM copies customer-specific historical information",
    3: "LLM chooses wrong historical resolution",
    4: "LLM produces generic response despite useful evidence",
    5: "LLM misunderstands the intent",
    6: "Retrieved evidence itself is poor",
    7: "Evidence insufficient but model answers anyway",
    8: "Response technically grounded but not helpful",
}


def main() -> int:
    predictions_path = (
        PROJECT_ROOT / "evaluation" / "results" / "grounded_reply_predictions.jsonl"
    )
    grounding_path = (
        PROJECT_ROOT / "evaluation" / "results" / "grounding_checks.json"
    )

    if not predictions_path.exists():
        print(f"Error: {predictions_path} not found.")
        print("Run: python scripts/evaluate_grounded_replies.py")
        return 1

    print("=" * 60)
    print("GROUNDED REPLY FAILURE ANALYSIS")
    print("=" * 60)

    # Load predictions
    predictions = []
    with open(predictions_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                predictions.append(json.loads(line))

    print(f"\nTotal predictions: {len(predictions)}")

    # Categorize
    status_counts = Counter()
    risk_counts = Counter()
    category_counts = Counter()

    insufficient_evidence_replies = []
    error_replies = []
    risky_replies = []

    for pred in predictions:
        status = pred.get("status", "unknown")
        status_counts[status] += 1

        reply = pred.get("reply")
        risk_flags = pred.get("risk_flags", [])

        if risk_flags:
            for flag in risk_flags:
                risk_counts[flag] += 1
            risky_replies.append(pred)

        if status == "insufficient_evidence" and reply:
            insufficient_evidence_replies.append(pred)
            category_counts[7] += 1

        if status == "provider_error":
            error_replies.append(pred)

    # Load grounding checks if available
    grounding_issues = []
    if grounding_path.exists():
        with open(grounding_path, "r", encoding="utf-8") as f:
            grounding_data = json.load(f)
        for gc in grounding_data:
            if not gc.get("passed", True):
                grounding_issues.append(gc)
                for issue in gc.get("issues", []):
                    if "PII" in issue:
                        category_counts[2] += 1
                    elif "Unsupported" in issue:
                        category_counts[1] += 1
                    elif "overlap" in issue.lower():
                        category_counts[4] += 1

    # Summary
    print(f"\n--- Status Distribution ---")
    for status, count in status_counts.most_common():
        print(f"  {status}: {count}")

    if risk_counts:
        print(f"\n--- Risk Flags ---")
        for flag, count in risk_counts.most_common():
            print(f"  {flag}: {count}")

    if grounding_issues:
        print(f"\n--- Grounding Issues ---")
        print(f"  Total issues: {len(grounding_issues)}")
        for gi in grounding_issues[:5]:
            print(f"\n  Query: {gi.get('customer_message', '')[:80]}...")
            print(f"  Reply: {gi.get('reply', '')[:80]}...")
            print(f"  Issues: {gi.get('issues', [])}")

    if category_counts:
        print(f"\n--- Failure Categories ---")
        for cat_id, count in category_counts.most_common():
            print(f"  Category {cat_id} ({FAILURE_CATEGORIES.get(cat_id, 'Unknown')}): {count}")

    # Sample failures
    print(f"\n--- Sample Provider Errors ---")
    for pred in error_replies[:3]:
        print(f"\n  Query: {pred.get('customer_message', '')[:80]}...")
        meta = pred.get("metadata", {})
        print(f"  Error: {meta.get('error_type')}: {meta.get('error_message', '')[:100]}")

    # Save results
    output_path = PROJECT_ROOT / "evaluation" / "results" / "grounded_reply_failure_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_predictions": len(predictions),
            "status_distribution": dict(status_counts),
            "risk_flags": dict(risk_counts),
            "failure_categories": dict(category_counts),
            "category_descriptions": FAILURE_CATEGORIES,
            "n_grounding_issues": len(grounding_issues),
            "n_provider_errors": len(error_replies),
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    print(f"\n{'=' * 60}")
    print("FAILURE ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

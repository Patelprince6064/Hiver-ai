#!/usr/bin/env python3
"""Analyze grounding verification failures.

Usage:
    python scripts/analyze_grounding_failures.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


FAILURE_CATEGORIES = {
    1: "Unsupported factual claim (hallucination)",
    2: "Unsupported high-risk claim (price, timeline, guarantee)",
    3: "Unsupported URL",
    4: "Historical identifier/PII leakage",
    5: "Unsupported numeric claim",
    6: "Low semantic grounding score",
    7: "No evidence available",
    8: "Unsupported contact method",
}


def main() -> int:
    ver_path = PROJECT_ROOT / "evaluation" / "results" / "grounding_verifications.jsonl"

    if not ver_path.exists():
        print(f"Error: {ver_path} not found.")
        print("Run: python scripts/evaluate_grounding.py")
        return 1

    print("=" * 60)
    print("GROUNDING FAILURE ANALYSIS")
    print("=" * 60)

    verifications = []
    with open(ver_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                verifications.append(json.loads(line))

    print(f"\nTotal verifications: {len(verifications)}")

    status_counts = Counter()
    risk_counts = Counter()
    category_counts = Counter()
    claim_type_counts = Counter()
    unsupported_samples = []

    for v in verifications:
        status = v.get("final_status", v.get("status", "unknown"))
        status_counts[status] += 1

        for flag in v.get("risk_flags", []):
            risk_counts[flag] += 1
            if "unsupported_high_risk" in flag:
                category_counts[2] += 1
            elif "unsupported_url" in flag:
                category_counts[3] += 1
            elif "contains_order_id" in flag or "historical_pii" in flag:
                category_counts[4] += 1
            elif "unsupported_numeric" in flag:
                category_counts[5] += 1
            elif "low_semantic_grounding" in flag:
                category_counts[6] += 1

        if v.get("unsupported_claims"):
            unsupported_samples.append(v)
            for sc in v["unsupported_claims"]:
                claim_type = sc.get("type", "unknown")
                claim_type_counts[claim_type] += 1
                if claim_type in ("price", "guarantee", "timeline", "refund"):
                    category_counts[1] += 1
                elif claim_type == "contact_method":
                    category_counts[8] += 1

        if v.get("status") == "insufficient_evidence":
            category_counts[7] += 1

    print(f"\n--- Status Distribution ---")
    for status, count in status_counts.most_common():
        print(f"  {status}: {count}")

    if risk_counts:
        print(f"\n--- Risk Flags ---")
        for flag, count in risk_counts.most_common():
            print(f"  {flag}: {count}")

    if claim_type_counts:
        print(f"\n--- Unsupported Claim Types ---")
        for ctype, count in claim_type_counts.most_common():
            print(f"  {ctype}: {count}")

    if category_counts:
        print(f"\n--- Failure Categories ---")
        for cat_id, count in category_counts.most_common():
            print(f"  Category {cat_id} ({FAILURE_CATEGORIES.get(cat_id, 'Unknown')}): {count}")

    if unsupported_samples:
        print(f"\n--- Sample Unsupported Claims ---")
        for sample in unsupported_samples[:5]:
            print(f"\n  Query: {sample.get('customer_message', '')[:80]}...")
            print(f"  Reply: {sample.get('reply', '')[:80]}...")
            for sc in sample.get("unsupported_claims", [])[:2]:
                print(f"    - {sc.get('claim', '')[:60]} (type: {sc.get('type', 'unknown')})")

    output_path = PROJECT_ROOT / "evaluation" / "results" / "grounding_failure_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_verifications": len(verifications),
            "status_distribution": dict(status_counts),
            "risk_flags": dict(risk_counts),
            "claim_types": dict(claim_type_counts),
            "failure_categories": dict(category_counts),
            "category_descriptions": FAILURE_CATEGORIES,
            "n_unsupported_samples": len(unsupported_samples),
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    print(f"\n{'=' * 60}")
    print("FAILURE ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

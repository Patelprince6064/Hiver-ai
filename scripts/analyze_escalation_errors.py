#!/usr/bin/env python3
"""Analyze escalation errors.

Usage:
    python scripts/analyze_escalation_errors.py
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze escalation errors")
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
    print("ESCALATION ERROR ANALYSIS")
    print("=" * 60)
    print(f"\nTotal decisions: {len(results)}")

    reason_code_counts = defaultdict(int)
    risk_level_counts = defaultdict(int)
    signal_patterns = defaultdict(int)

    escalation_examples = []
    auto_handle_examples = []

    for r in results:
        decision = r["decision"]
        risk_level = r.get("risk_level", "LOW")
        reason_codes = r.get("reason_codes", [])
        signals = r.get("signals", {})

        risk_level_counts[risk_level] += 1

        for rc in reason_codes:
            reason_code_counts[rc] += 1

        if decision == "ESCALATE_TO_HUMAN":
            if len(escalation_examples) < 10:
                escalation_examples.append({
                    "query_id": r["query_id"],
                    "customer_message": r["customer_message"][:150],
                    "reason_codes": reason_codes,
                    "risk_level": risk_level,
                    "signals": {
                        "intent_confidence": signals.get("intent_confidence"),
                        "retrieval_available": signals.get("retrieval_available"),
                        "grounding_status": signals.get("grounding_status"),
                        "evidence_count": signals.get("evidence_count"),
                    },
                })
        else:
            if len(auto_handle_examples) < 5:
                auto_handle_examples.append({
                    "query_id": r["query_id"],
                    "customer_message": r["customer_message"][:150],
                    "signals": {
                        "intent_confidence": signals.get("intent_confidence"),
                        "retrieval_available": signals.get("retrieval_available"),
                        "grounding_status": signals.get("grounding_status"),
                    },
                })

        if signals.get("retrieval_available") and decision == "ESCALATE_TO_HUMAN":
            signal_patterns["has_retrieval_but_escalated"] += 1
        if not signals.get("retrieval_available") and decision == "AUTO_HANDLE":
            signal_patterns["no_retrieval_but_auto_handle"] += 1
        if signals.get("grounding_status") == "pass" and decision == "ESCALATE_TO_HUMAN":
            signal_patterns["grounding_pass_but_escalated"] += 1

    print(f"\n--- Reason Code Distribution ---")
    for rc, count in sorted(reason_code_counts.items(), key=lambda x: -x[1]):
        print(f"  {rc}: {count}")

    print(f"\n--- Risk Level Distribution ---")
    for level, count in sorted(risk_level_counts.items()):
        print(f"  {level}: {count}")

    print(f"\n--- Signal Patterns ---")
    for pattern, count in sorted(signal_patterns.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")

    print(f"\n--- Sample Escalation Cases ---")
    for ex in escalation_examples[:5]:
        print(f"\n  [{ex['query_id']}] {ex['customer_message']}")
        print(f"    Reasons: {', '.join(ex['reason_codes'])}")
        print(f"    Risk: {ex['risk_level']}")
        print(f"    Signals: {ex['signals']}")

    analysis = {
        "n_total": len(results),
        "reason_code_distribution": dict(reason_code_counts),
        "risk_level_distribution": dict(risk_level_counts),
        "signal_patterns": dict(signal_patterns),
        "escalation_examples": escalation_examples,
        "auto_handle_examples": auto_handle_examples,
    }

    analysis_path = output_dir / "escalation_error_analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {analysis_path}")

    print(f"\n{'=' * 60}")
    print("ERROR ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

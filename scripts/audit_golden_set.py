#!/usr/bin/env python3
"""Audit the golden evaluation set.

This script checks:
- Total examples
- Intent counts and percentages
- Ambiguous count
- Low-confidence count
- Missing labels
- Duplicate IDs
- Duplicate messages
- Missing source references

Usage:
    python scripts/audit_golden_set.py
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.golden_schema import load_golden_set, validate_golden_set


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()

    # Find golden set
    golden_path = project_root / "data" / "golden" / "golden_set.jsonl"
    if not golden_path.exists():
        print("Error: No golden set found.")
        print("Run annotation first: python scripts/annotate_golden.py")
        return 1

    # Load golden set
    examples = load_golden_set(golden_path)
    print(f"Loaded {len(examples)} golden examples.")

    # Load taxonomy for validation
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    taxonomy_path = selected_brand_dir / "intent_taxonomy.json"
    valid_intents = set()
    if taxonomy_path.exists():
        with open(taxonomy_path, "r") as f:
            taxonomy = json.load(f)
        valid_intents = {intent["name"] for intent in taxonomy.get("intents", [])}

    # Validate
    report = validate_golden_set(examples, valid_intents)

    # Additional statistics
    intent_counts = Counter(e.get("gold_intent", "") for e in examples)
    total = len(examples)

    # Confidence distribution
    confidences = Counter(e.get("intent_confidence", "UNKNOWN") for e in examples)

    # Ambiguous count
    ambiguous_count = sum(1 for e in examples if e.get("ambiguous", False))

    # Missing labels
    missing_labels = sum(1 for e in examples if not e.get("gold_intent"))

    # Duplicate messages
    messages = [e.get("customer_message", "") for e in examples]
    duplicate_messages = sum(1 for msg in messages if messages.count(msg) > 1)

    # Missing source references
    missing_conversation_id = sum(1 for e in examples if not e.get("conversation_id"))
    missing_message_id = sum(1 for e in examples if not e.get("message_id"))

    # Build statistics
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_examples": total,
        "valid": report["valid"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "intent_distribution": {
            intent: {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0,
            }
            for intent, count in intent_counts.most_common()
        },
        "confidence_distribution": dict(confidences),
        "ambiguous_count": ambiguous_count,
        "ambiguous_percentage": round(ambiguous_count / total * 100, 1) if total > 0 else 0,
        "missing_labels": missing_labels,
        "duplicate_messages": duplicate_messages,
        "missing_conversation_id": missing_conversation_id,
        "missing_message_id": missing_message_id,
    }

    # Print report
    print("\n" + "=" * 70)
    print("GOLDEN SET AUDIT REPORT")
    print("=" * 70)

    print(f"\nTotal examples: {total}")
    print(f"Valid: {'YES' if report['valid'] else 'NO'}")

    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report["errors"][:10]:
            print(f"  - {error}")

    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report["warnings"][:10]:
            print(f"  - {warning}")

    print(f"\nIntent Distribution:")
    for intent, info in stats["intent_distribution"].items():
        print(f"  {intent}: {info['count']} ({info['percentage']}%)")

    print(f"\nConfidence Distribution:")
    for conf, count in stats["confidence_distribution"].items():
        print(f"  {conf}: {count}")

    print(f"\nAmbiguous: {ambiguous_count} ({stats['ambiguous_percentage']}%)")
    print(f"Missing labels: {missing_labels}")
    print(f"Duplicate messages: {duplicate_messages}")
    print(f"Missing conversation_id: {missing_conversation_id}")
    print(f"Missing message_id: {missing_message_id}")

    # Save statistics
    stats_path = project_root / "data" / "golden" / "golden_set_statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nStatistics saved to: {stats_path}")

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

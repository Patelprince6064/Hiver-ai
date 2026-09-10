#!/usr/bin/env python3
"""Validate knowledge base schema and integrity.

Usage:
    python scripts/validate_knowledge_base.py
"""

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.knowledge_schema import validate_knowledge_base


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "knowledge_base.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()

    # Load knowledge base
    kb_path = project_root / "data" / "processed" / "knowledge_base.jsonl"
    if not kb_path.exists():
        print("Error: Knowledge base not found.")
        print("Run: python scripts/build_knowledge_base.py")
        return 1

    records = []
    with open(kb_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    return 1

    print(f"Loaded {len(records):,} knowledge records")

    # Load valid intents from taxonomy if available
    valid_intents = None
    taxonomy_path = project_root / "data" / "interim" / "selected_brand" / "intent_taxonomy.json"
    if taxonomy_path.exists():
        with open(taxonomy_path, "r") as f:
            taxonomy = json.load(f)
        valid_intents = {intent["name"] for intent in taxonomy.get("intents", [])}
        print(f"Loaded {len(valid_intents)} valid intents")

    # Load valid resolutions from config
    valid_resolutions = set(config.get("resolution_types", []))
    print(f"Loaded {len(valid_resolutions)} valid resolution types")

    # Validate
    report = validate_knowledge_base(records, valid_intents, valid_resolutions)

    # Print report
    print(f"\n{'='*70}")
    print("KNOWLEDGE BASE VALIDATION REPORT")
    print(f"{'='*70}")

    print(f"\nTotal records: {report['total_examples'] if 'total_examples' in report else report['total_records']}")
    print(f"Valid: {'YES' if report['valid'] else 'NO'}")

    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report["errors"][:20]:
            print(f"  - {error}")

    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report["warnings"][:20]:
            print(f"  - {warning}")

    if report["valid"]:
        print(f"\n✓ Validation PASSED.")
        return 0
    else:
        print(f"\n✗ Validation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

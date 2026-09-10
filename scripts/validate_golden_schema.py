#!/usr/bin/env python3
"""Validate the golden evaluation set schema.

This script checks that all golden-set examples conform to the schema.

Usage:
    python scripts/validate_golden_schema.py
    python scripts/validate_golden_schema.py --strict
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.golden_schema import (
    load_golden_set,
    validate_golden_set,
)


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate golden-set schema.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = parser.parse_args()

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

    # Load valid intents
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    taxonomy_path = selected_brand_dir / "intent_taxonomy.json"
    valid_intents = set()
    if taxonomy_path.exists():
        with open(taxonomy_path, "r") as f:
            taxonomy = json.load(f)
        valid_intents = {intent["name"] for intent in taxonomy.get("intents", [])}

    # Validate
    report = validate_golden_set(examples, valid_intents=valid_intents)

    # Print report
    print("\n" + "=" * 70)
    print("SCHEMA VALIDATION REPORT")
    print("=" * 70)

    print(f"\nTotal examples: {report['total_examples']}")
    print(f"Valid: {'YES' if report['valid'] else 'NO'}")

    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report["errors"][:20]:
            print(f"  - {error}")

    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report["warnings"][:20]:
            print(f"  - {warning}")

    # Determine exit code
    if not report["valid"]:
        print("\n✗ Validation FAILED.")
        return 1
    elif args.strict and report["warnings"]:
        print("\n✗ Validation FAILED (strict mode: warnings treated as errors).")
        return 1
    else:
        print("\n✓ Validation PASSED.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

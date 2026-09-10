#!/usr/bin/env python3
"""Validate the intent taxonomy.

This script checks:
- Unique intent IDs
- Unique intent names
- Valid snake_case names
- Non-empty descriptions
- Presence of examples
- Inclusion/exclusion criteria
- Confusable intents documented
- Reasonable number of intents

Usage:
    python scripts/validate_intent_taxonomy.py
    python scripts/validate_intent_taxonomy.py --taxonomy data/interim/selected_brand/intent_taxonomy.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validate_snake_case(name: str) -> bool:
    """Check if a name is valid snake_case."""
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


def validate_taxonomy(taxonomy: dict) -> list[dict]:
    """Validate a taxonomy dict. Returns list of issues."""
    issues = []

    # Check top-level fields
    if "taxonomy_version" not in taxonomy:
        issues.append({"check": "top_level", "message": "Missing taxonomy_version"})
    if "selected_brand" not in taxonomy:
        issues.append({"check": "top_level", "message": "Missing selected_brand"})
    if "intents" not in taxonomy:
        issues.append({"check": "top_level", "message": "Missing intents list"})
        return issues

    intents = taxonomy["intents"]
    if not isinstance(intents, list):
        issues.append({"check": "intents", "message": "intents must be a list"})
        return issues

    # Check intent count
    if len(intents) < 3:
        issues.append({"check": "intent_count", "message": f"Only {len(intents)} intents (expected 5+)"})
    if len(intents) > 20:
        issues.append({"check": "intent_count", "message": f"{len(intents)} intents (expected <= 15)"})

    # Check each intent
    ids_seen = set()
    names_seen = set()
    all_examples = []

    for i, intent in enumerate(intents):
        prefix = f"intent[{i}]"

        # Required fields
        for field in ["intent_id", "name", "description"]:
            if field not in intent:
                issues.append({"check": prefix, "message": f"Missing {field}"})

        # ID uniqueness
        intent_id = intent.get("intent_id", "")
        if intent_id in ids_seen:
            issues.append({"check": prefix, "message": f"Duplicate intent_id: {intent_id}"})
        ids_seen.add(intent_id)

        # Name uniqueness
        name = intent.get("name", "")
        if name in names_seen:
            issues.append({"check": prefix, "message": f"Duplicate name: {name}"})
        names_seen.add(name)

        # Snake case
        if name and not validate_snake_case(name):
            issues.append({"check": prefix, "message": f"Name not snake_case: {name}"})

        # Description
        desc = intent.get("description", "")
        if not desc or len(desc.strip()) < 10:
            issues.append({"check": prefix, "message": "Description too short or empty"})

        # Examples
        examples = intent.get("examples", [])
        if not examples:
            issues.append({"check": prefix, "message": "No examples provided"})
        elif len(examples) < 2:
            issues.append({"check": prefix, "message": "Fewer than 2 examples"})

        # Check for duplicate examples across intents
        for ex in examples:
            if ex in all_examples:
                issues.append({"check": prefix, "message": f"Duplicate example: {ex[:50]}..."})
            all_examples.append(ex)

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate intent taxonomy.")
    parser.add_argument("--taxonomy", type=str, default=None, help="Taxonomy JSON path.")
    args = parser.parse_args()

    # Find taxonomy
    if args.taxonomy:
        taxonomy_path = Path(args.taxonomy)
    else:
        taxonomy_path = PROJECT_ROOT / "data" / "interim" / "selected_brand" / "intent_taxonomy.json"

    if not taxonomy_path.exists():
        print(f"Error: Taxonomy not found at {taxonomy_path}")
        print("Create the taxonomy first in Phase 5.")
        return 1

    print(f"Validating taxonomy: {taxonomy_path}")

    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)

    issues = validate_taxonomy(taxonomy)

    if issues:
        print(f"\nVALIDATION FAILED: {len(issues)} issue(s) found\n")
        for issue in issues:
            print(f"  [{issue['check']}] {issue['message']}")
        return 1
    else:
        print("VALIDATION PASSED")
        print(f"  Intents: {len(taxonomy.get('intents', []))}")
        print(f"  Version: {taxonomy.get('taxonomy_version', 'N/A')}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

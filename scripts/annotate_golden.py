#!/usr/bin/env python3
"""Simple terminal-based annotation tool for the golden evaluation set.

This script provides a lightweight interface for human annotation of
customer messages with intent labels.

Usage:
    python scripts/annotate_golden.py
    python scripts/annotate_golden.py --start 0 --end 50
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.golden_schema import load_golden_set, save_golden_set


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_taxonomy(taxonomy_path: Path) -> list[dict]:
    """Load intent taxonomy."""
    if not taxonomy_path.exists():
        return []
    with open(taxonomy_path, "r") as f:
        data = json.load(f)
    return data.get("intents", [])


def display_message(example: dict, index: int, total: int) -> None:
    """Display a message for annotation."""
    print("\n" + "=" * 70)
    print(f"Example {index + 1} of {total}")
    print("=" * 70)
    print(f"\nGolden ID: {example.get('golden_id', 'N/A')}")
    print(f"Conversation ID: {example.get('conversation_id', 'N/A')}")
    print(f"\nCustomer Message:")
    print(f"  {example.get('customer_message', '')}")

    context = example.get("context_messages", [])
    if context:
        print(f"\nContext ({len(context)} messages):")
        for msg in context[-3:]:  # Show last 3 context messages
            print(f"  > {msg[:100]}...")

    print(f"\nSampling Category: {example.get('sampling_category', 'N/A')}")


def display_intents(intents: list[dict]) -> None:
    """Display available intents."""
    print("\nAvailable Intents:")
    print("-" * 40)
    for i, intent in enumerate(intents, 1):
        print(f"  {i:2d}. {intent['name']}")
        print(f"      {intent.get('description', '')[:60]}")
    print(f"  {len(intents) + 1:2d}. AMBIGUOUS (cannot determine intent)")
    print(f"  {len(intents) + 2:2d}. SKIP (skip this example)")
    print("-" * 40)


def get_annotation(intents: list[dict]) -> dict | None:
    """Get annotation from user."""
    while True:
        try:
            choice = input("\nEnter intent number (or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                return None

            idx = int(choice) - 1

            if idx == len(intents):
                # Ambiguous
                return {
                    "gold_intent": "ambiguous",
                    "intent_confidence": "LOW",
                    "ambiguous": True,
                    "label_notes": input("Why ambiguous? ").strip(),
                }
            elif idx == len(intents) + 1:
                # Skip
                return {"skip": True}
            elif 0 <= idx < len(intents):
                # Valid intent
                intent = intents[idx]
                confidence = input("Confidence (H/M/L, default=H): ").strip().upper()
                if confidence not in ("H", "M", "L"):
                    confidence = "H"

                notes = input("Notes (optional): ").strip()

                return {
                    "gold_intent": intent["name"],
                    "intent_confidence": {"H": "HIGH", "M": "MEDIUM", "L": "LOW"}[confidence],
                    "ambiguous": False,
                    "label_notes": notes,
                }
            else:
                print(f"Invalid choice. Enter 1-{len(intents) + 2}.")
        except ValueError:
            print("Invalid input. Enter a number.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Annotate golden-set examples.")
    parser.add_argument("--start", type=int, default=0, help="Start index.")
    parser.add_argument("--end", type=int, default=None, help="End index.")
    parser.add_argument("--dry-run", action="store_true", help="Don't save annotations.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Find golden candidates
    candidates_path = project_root / "data" / "golden" / "golden_candidates.csv"
    if not candidates_path.exists():
        print("Error: No candidate pool found.")
        print("Run: python scripts/build_golden_candidates.py")
        return 1

    # Load candidates
    import pandas as pd
    candidates_df = pd.read_csv(candidates_path)
    candidates = candidates_df.to_dict(orient="records")
    print(f"Loaded {len(candidates)} candidates.")

    # Load taxonomy
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    taxonomy_path = selected_brand_dir / "intent_taxonomy.json"
    intents = load_taxonomy(taxonomy_path)

    if not intents:
        print("Error: No intent taxonomy found.")
        print("Run Phase 5 to create the taxonomy.")
        return 1

    print(f"Loaded {len(intents)} intents.")

    # Determine range
    end = args.end or len(candidates)
    end = min(end, len(candidates))
    candidates_to_annotate = candidates[args.start:end]

    print(f"\nAnnotating examples {args.start + 1} to {end}")

    # Display intents
    display_intents(intents)

    # Annotate
    annotated = []
    skipped = 0

    for i, example in enumerate(candidates_to_annotate):
        global_idx = args.start + i

        # Display message
        display_message(example, i, len(candidates_to_annotate))

        # Get annotation
        annotation = get_annotation(intents)

        if annotation is None:
            print("\nQuitting annotation session.")
            break

        if annotation.get("skip"):
            skipped += 1
            # Keep original empty fields
            annotated.append(example)
            continue

        # Apply annotation
        example.update(annotation)
        annotated.append(example)

        print(f"  -> Labeled as: {annotation['gold_intent']}")

    # Print summary
    print(f"\n--- Annotation Session Summary ---")
    print(f"Annotated: {len(annotated) - skipped}")
    print(f"Skipped: {skipped}")

    # Save if not dry run
    if not args.dry_run and annotated:
        # Update the full candidates file
        golden_path = project_root / "data" / "golden" / "golden_set.jsonl"

        # Load existing if any
        existing = []
        if golden_path.exists():
            existing = load_golden_set(golden_path)

        # Merge (replace existing entries with same golden_id)
        existing_ids = {e["golden_id"] for e in existing}
        new_annotated = [a for a in annotated if a.get("gold_intent") and a["golden_id"] not in existing_ids]
        updated = [a for a in annotated if a.get("gold_intent")] + [
            e for e in existing if e["golden_id"] not in {a["golden_id"] for a in annotated}
        ]

        save_golden_set(updated, golden_path)
        print(f"\nSaved {len(updated)} examples to {golden_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

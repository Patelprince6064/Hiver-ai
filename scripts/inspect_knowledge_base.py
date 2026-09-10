#!/usr/bin/env python3
"""Inspect knowledge base records.

Usage:
    python scripts/inspect_knowledge_base.py --n 30 --seed 42
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect knowledge base.")
    parser.add_argument("--n", type=int, default=30, help="Number of samples.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    project_root = find_project_root()

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
                records.append(json.loads(line))

    print(f"Loaded {len(records):,} knowledge records")

    # Sample
    rng = np.random.RandomState(args.seed)
    n = min(args.n, len(records))
    indices = rng.choice(len(records), size=n, replace=False)
    samples = [records[i] for i in indices]

    # Display
    print(f"\n{'='*80}")
    print(f"KNOWLEDGE BASE SAMPLE ({n} records)")
    print(f"{'='*80}")

    for i, record in enumerate(samples):
        print(f"\n--- Record {i+1} ---")
        print(f"Knowledge ID: {record.get('knowledge_id')}")
        print(f"Conversation ID: {record.get('conversation_id')}")
        print(f"\nCustomer Message:")
        print(f"  {record.get('customer_message', '')[:150]}")
        print(f"\nSupport Response:")
        print(f"  {record.get('support_response', '')[:150]}")
        print(f"\nIntent: {record.get('intent', 'N/A')} (confidence: {record.get('intent_confidence', 'N/A')})")
        print(f"Resolution Type: {record.get('resolution_type')}")
        print(f"Quality Flags: {record.get('quality_flags', [])}")
        print(f"Quality Category: {record.get('quality_category')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

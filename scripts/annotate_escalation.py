#!/usr/bin/env python3
"""Prepare escalation evaluation dataset.

Usage:
    python scripts/annotate_escalation.py [--split dev] [--seed 42]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare escalation evaluation dataset")
    parser.add_argument("--split", default="dev", help="Data split")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n-queries", type=int, default=150, help="Number of queries")
    args = parser.parse_args()

    config_path = PROJECT_ROOT / "configs" / "escalation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    output_dir = PROJECT_ROOT / config["escalation"]["eval"]["eval_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PREPARE ESCALATION EVALUATION DATASET")
    print("=" * 60)

    split_path = PROJECT_ROOT / "data" / "processed" / "splits" / f"{args.split}.csv"
    if not split_path.exists():
        print(f"\nSplit file not found: {split_path}")
        print("Run: python scripts/create_model_splits.py")
        return 1

    import pandas as pd
    import numpy as np

    df = pd.read_csv(split_path)
    print(f"\nLoaded {args.split} split: {len(df)} examples")

    np.random.seed(args.seed)
    n_queries = min(args.n_queries, len(df))
    indices = np.random.choice(len(df), size=n_queries, replace=False)
    sampled = df.iloc[indices].reset_index(drop=True)

    records = []
    for i, row in sampled.iterrows():
        records.append({
            "query_id": f"esc_{i:04d}",
            "customer_message": str(row["text"]),
            "intent": str(row.get("label", "")) if pd.notna(row.get("label")) else "",
            "split": args.split,
            "gold_decision": None,
            "gold_reason_codes": [],
            "annotator_id": None,
            "notes": "",
        })

    manifest_path = output_dir / "evaluation_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nManifest: {manifest_path}")

    meta = {
        "version": "1.0",
        "n_queries": n_queries,
        "seed": args.seed,
        "split": args.split,
        "has_gold_labels": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = output_dir / "manifest_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata: {meta_path}")

    print(f"\n{'=' * 60}")
    print("PREPARATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Queries: {n_queries}")
    print(f"Gold labels: NOT YET ANNOTATED")
    print(f"\nTo annotate: python scripts/annotate_escalation.py --interactive")
    return 0


if __name__ == "__main__":
    sys.exit(main())

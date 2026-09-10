#!/usr/bin/env python3
"""Prepare the reply quality evaluation dataset.

Creates an evaluation manifest with queries sampled from the dev split.
Uses deterministic sampling with seed 42.

Usage:
    python scripts/prepare_reply_evaluation.py [--n-queries 150] [--split dev] [--seed 42]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config() -> dict:
    with open(PROJECT_ROOT / "configs" / "project.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare reply evaluation dataset")
    parser.add_argument("--n-queries", type=int, default=150, help="Number of evaluation queries")
    parser.add_argument("--split", default="dev", help="Data split to sample from")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / "data" / "interim" / "reply_eval"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PREPARE REPLY EVALUATION DATASET")
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

    n_available = len(df)
    n_queries = min(args.n_queries, n_available)

    if n_queries < args.n_queries:
        print(f"Warning: Only {n_available} examples available, using all")

    indices = np.random.choice(n_available, size=n_queries, replace=False)
    sampled = df.iloc[indices].reset_index(drop=True)

    intent_col = "label" if "label" in sampled.columns else None
    conv_col = "conversation_id" if "conversation_id" in sampled.columns else None
    msg_col = "message_id" if "message_id" in sampled.columns else None

    records = []
    for i, row in sampled.iterrows():
        query_id = f"q_{i:04d}"
        record = {
            "query_id": query_id,
            "conversation_id": str(row[conv_col]) if conv_col and pd.notna(row.get(conv_col)) else "",
            "message_id": str(row[msg_col]) if msg_col and pd.notna(row.get(msg_col)) else "",
            "customer_message": str(row["text"]),
            "intent": str(row[intent_col]) if intent_col and pd.notna(row.get(intent_col)) else "",
            "split": args.split,
        }
        records.append(record)

    manifest_path = output_dir / "evaluation_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nManifest: {manifest_path}")

    intent_dist = {}
    for rec in records:
        intent = rec["intent"] or "unknown"
        intent_dist[intent] = intent_dist.get(intent, 0) + 1

    splits = {args.split: n_queries}

    manifest_meta = {
        "version": "1.0",
        "n_queries": n_queries,
        "seed": args.seed,
        "splits": splits,
        "intent_distribution": intent_dist,
        "source_file": str(split_path.name),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = output_dir / "manifest_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(manifest_meta, f, indent=2)
    print(f"Metadata: {meta_path}")

    print(f"\n--- Summary ---")
    print(f"Queries: {n_queries}")
    print(f"Split: {args.split}")
    print(f"Seed: {args.seed}")
    print(f"Intents: {len(intent_dist)}")
    for intent, count in sorted(intent_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"  {intent}: {count}")

    print(f"\n{'=' * 60}")
    print("PREPARATION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

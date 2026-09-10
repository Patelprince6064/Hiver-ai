#!/usr/bin/env python3
"""Prepare the intent-discovery dataset.

This script:
1. Loads selected-brand conversations
2. Extracts customer messages
3. Filters unusable messages
4. Creates a deterministic sample for discovery
5. Saves the result for intent exploration

Usage:
    python scripts/prepare_intent_discovery.py
    python scripts/prepare_intent_discovery.py --sample-size 5000
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.eda_utils import detect_columns
from src.intents.message_extraction import (
    create_intent_discovery_dataset,
    analyze_text_quality,
    identify_customer_messages,
)


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare intent-discovery dataset.")
    parser.add_argument("--sample-size", type=int, default=5000, help="Sample size for discovery.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Find selected brand
    selected_brand = config.get("dataset", {}).get("selected_brand")
    if not selected_brand:
        print("Error: No brand selected.")
        print("Run: python scripts/compute_brand_statistics.py")
        print("Then: python scripts/extract_selected_brand.py")
        return 1

    # Find selected brand data
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    messages_path = selected_brand_dir / "messages.csv"

    if not messages_path.exists():
        print(f"Error: No messages found at {messages_path}")
        print("Run: python scripts/extract_selected_brand.py")
        return 1

    print(f"Selected brand: {selected_brand}")
    print(f"Loading messages from: {messages_path}")

    # Load data
    df = pd.read_csv(messages_path, low_memory=False)
    print(f"Loaded {len(df):,} messages.")

    # Detect columns
    col_map = detect_columns(df)
    text_col = col_map.get("text")
    if not text_col:
        print("Error: No text column detected.")
        print(f"Available columns: {list(df.columns)}")
        return 1

    print(f"Text column: {text_col}")

    # Identify customer messages
    customer_mask = identify_customer_messages(df, col_map)
    n_customer = customer_mask.sum()
    n_total = len(df)
    print(f"Customer messages: {n_customer:,} ({n_customer/n_total*100:.1f}%)")

    # Create intent discovery dataset
    print(f"\nCreating intent discovery dataset (sample_size={args.sample_size})...")
    discovery_df = create_intent_discovery_dataset(
        df, col_map, text_col,
        sample_size=args.sample_size,
        seed=args.seed,
    )
    print(f"Discovery dataset: {len(discovery_df):,} messages")

    # Analyze text quality
    quality = analyze_text_quality(discovery_df, text_col)
    print(f"\nText quality:")
    for k, v in quality.items():
        print(f"  {k}: {v}")

    # Save
    output_dir = selected_brand_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "intent_discovery_messages.csv"
    discovery_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")

    # Save metadata
    metadata = {
        "selected_brand": selected_brand,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_brand_messages": n_total,
        "customer_messages": int(n_customer),
        "discovery_sample_size": len(discovery_df),
        "sample_size_requested": args.sample_size,
        "seed": args.seed,
        "text_quality": quality,
        "columns_used": col_map,
    }

    metadata_path = output_dir / "intent_discovery_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

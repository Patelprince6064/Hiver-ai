#!/usr/bin/env python3
"""Create leakage-safe train/dev/test splits.

Splits by conversation to prevent leakage.

Usage:
    python scripts/create_model_splits.py --seed 42
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def create_splits(
    df: pd.DataFrame,
    text_col: str,
    label_col: str,
    conv_col: str | None,
    train_ratio: float = 0.70,
    dev_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create train/dev/test splits by conversation."""
    rng = np.random.RandomState(seed)

    if conv_col and conv_col in df.columns:
        # Split by conversation
        conversations = df[conv_col].dropna().unique()
        rng.shuffle(conversations)
        n = len(conversations)
        n_train = int(n * train_ratio)
        n_dev = int(n * dev_ratio)

        train_convs = set(conversations[:n_train])
        dev_convs = set(conversations[n_train:n_train + n_dev])
        test_convs = set(conversations[n_train + n_dev:])

        train_df = df[df[conv_col].isin(train_convs)].copy()
        dev_df = df[df[conv_col].isin(dev_convs)].copy()
        test_df = df[df[conv_col].isin(test_convs)].copy()
    else:
        # Split by row (fallback)
        indices = np.arange(len(df))
        rng.shuffle(indices)
        n = len(indices)
        n_train = int(n * train_ratio)
        n_dev = int(n * dev_ratio)

        train_df = df.iloc[indices[:n_train]].copy()
        dev_df = df.iloc[indices[n_train:n_train + n_dev]].copy()
        test_df = df.iloc[indices[n_train + n_dev:]].copy()

    # Standardize columns
    for split_df in [train_df, dev_df, test_df]:
        if text_col in split_df.columns:
            split_df["text"] = split_df[text_col]
        if label_col in split_df.columns:
            split_df["label"] = split_df[label_col]

    return train_df, dev_df, test_df


def main() -> int:
    parser = argparse.ArgumentParser(description="Create model splits.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--dev-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Find selected brand
    selected_brand = config.get("dataset", {}).get("selected_brand")
    if not selected_brand:
        print("Error: No brand selected.")
        print("Run: python scripts/compute_brand_statistics.py")
        return 1

    # Load data
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    messages_path = selected_brand_dir / "messages.csv"
    if not messages_path.exists():
        print(f"Error: No messages found at {messages_path}")
        return 1

    print(f"Selected brand: {selected_brand}")
    df = pd.read_csv(messages_path, low_memory=False)
    print(f"Loaded {len(df):,} messages.")

    # Detect columns
    text_col = "text"
    label_col = "label"
    conv_col = "conversation_id"

    # Check if label column exists
    if label_col not in df.columns:
        print(f"Warning: Column '{label_col}' not found.")
        # Check for intent taxonomy
        taxonomy_path = selected_brand_dir / "intent_taxonomy.json"
        if taxonomy_path.exists():
            print("Intent taxonomy found. Labels will be assigned during annotation.")
        else:
            print("No intent taxonomy found. Creating splits with available columns.")
            # Use a placeholder label if needed
            if "gold_intent" in df.columns:
                label_col = "gold_intent"
            else:
                print("Error: No label column found.")
                return 1

    # Create splits
    print(f"\nCreating splits (seed={args.seed})...")
    print(f"  Train: {args.train_ratio:.0%}")
    print(f"  Dev: {args.dev_ratio:.0%}")
    print(f"  Test: {args.test_ratio:.0%}")

    train_df, dev_df, test_df = create_splits(
        df, text_col, label_col, conv_col,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    print(f"\nSplit sizes:")
    print(f"  Train: {len(train_df):,}")
    print(f"  Dev: {len(dev_df):,}")
    print(f"  Test: {len(test_df):,}")

    # Save splits
    output_dir = project_root / "data" / "processed" / "splits"
    output_dir.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(output_dir / "train.csv", index=False)
    dev_df.to_csv(output_dir / "dev.csv", index=False)
    test_df.to_csv(output_dir / "test.csv", index=False)

    # Save metadata
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "ratios": {
            "train": args.train_ratio,
            "dev": args.dev_ratio,
            "test": args.test_ratio,
        },
        "split_method": "conversation" if conv_col and conv_col in df.columns else "row",
        "total_examples": len(df),
        "splits": {
            "train": len(train_df),
            "dev": len(dev_df),
            "test": len(test_df),
        },
        "selected_brand": selected_brand,
    }

    with open(output_dir / "split_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSplits saved to: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

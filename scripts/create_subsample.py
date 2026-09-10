#!/usr/bin/env python3
"""Create a reproducible development subsample of the dataset.

This script creates a deterministic subsample of the dataset that:

1. Preserves conversation integrity (all messages from a conversation stay together)
2. Maintains reasonable brand distribution (if brand info exists)
3. Supports configurable target size
4. Uses a fixed random seed for reproducibility

Usage:

    python scripts/create_subsample.py --target-messages 25000 --seed 42

The subsample is saved to data/interim/development_sample.csv
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def find_project_root() -> Path:
    """Find the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def find_main_csv(raw_dir: Path) -> Path | None:
    """Find the main CSV file in data/raw/."""
    # Look for known dataset files
    candidates = ["twcs.csv"]

    for name in candidates:
        path = raw_dir / name
        if path.exists():
            return path

    # Fall back to any CSV file
    csv_files = sorted(raw_dir.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    return None


def load_dataset_in_chunks(filepath: Path, chunk_size: int = 50000) -> pd.DataFrame:
    """Load a large CSV file in chunks to manage memory."""
    chunks = []
    for chunk in pd.read_csv(filepath, chunksize=chunk_size, low_memory=False):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)


def identify_conversation_column(df: pd.DataFrame) -> str | None:
    """Identify the conversation/thread ID column."""
    # Known column names for this dataset
    candidates = ["conversation_id", "thread_id", "in_reply_to_tweet_id"]

    for col in candidates:
        if col in df.columns:
            return col

    # Look for ID-like columns
    for col in df.columns:
        if "conversation" in col.lower() or "thread" in col.lower():
            return col

    return None


def identify_brand_column(df: pd.DataFrame) -> str | None:
    """Identify the brand/company column."""
    candidates = ["brand", "company", "author_name", "inbound_author"]

    for col in candidates:
        if col in df.columns:
            return col

    # Look for brand-like columns
    for col in df.columns:
        if "brand" in col.lower() or "company" in col.lower():
            return col

    return None


def create_subsample(
    df: pd.DataFrame,
    target_messages: int,
    seed: int,
    conversation_col: str | None,
    brand_col: str | None,
) -> tuple[pd.DataFrame, dict]:
    """Create a subsample preserving conversation integrity.

    Returns:
        Tuple of (subsampled DataFrame, metadata dict)
    """
    rng = np.random.RandomState(seed)
    total_rows = len(df)

    if total_rows <= target_messages:
        return df, {
            "sampling_unit": "conversation",
            "random_seed": seed,
            "target_messages": target_messages,
            "actual_messages": total_rows,
            "conversation_integrity": True,
            "note": "Entire dataset is smaller than target size",
        }

    if conversation_col and conversation_col in df.columns:
        # Conversation-level sampling
        conversations = df[conversation_col].unique()
        n_conversations = len(conversations)

        # Estimate messages per conversation
        avg_msgs_per_conv = total_rows / n_conversations
        target_conversations = int(target_messages / avg_msgs_per_conv)

        # Sample conversations
        sampled_conv_ids = rng.choice(
            conversations,
            size=min(target_conversations, n_conversations),
            replace=False,
        )

        # Get all messages from sampled conversations
        mask = df[conversation_col].isin(sampled_conv_ids)
        subsample = df[mask].copy()

        # If too large, randomly remove conversations from the end
        if len(subsample) > target_messages * 1.5:
            # Re-sample with fewer conversations
            target_conversations = int(target_messages / avg_msgs_per_conv * 0.7)
            sampled_conv_ids = rng.choice(
                conversations,
                size=min(target_conversations, n_conversations),
                replace=False,
            )
            mask = df[conversation_col].isin(sampled_conv_ids)
            subsample = df[mask].copy()

        metadata = {
            "sampling_unit": "conversation",
            "random_seed": seed,
            "target_messages": target_messages,
            "actual_messages": len(subsample),
            "sampled_conversations": len(sampled_conv_ids),
            "total_conversations": n_conversations,
            "conversation_integrity": True,
        }
    else:
        # Row-level sampling (no conversation ID available)
        indices = rng.choice(total_rows, size=target_messages, replace=False)
        subsample = df.iloc[indices].copy()

        metadata = {
            "sampling_unit": "row",
            "random_seed": seed,
            "target_messages": target_messages,
            "actual_messages": len(subsample),
            "conversation_integrity": False,
            "note": "No conversation ID found; row-level sampling used",
        }

    # Preserve brand distribution info if available
    if brand_col and brand_col in subsample.columns:
        brand_counts = subsample[brand_col].value_counts().to_dict()
        metadata["brand_distribution"] = {str(k): int(v) for k, v in brand_counts.items()}

    return subsample, metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a reproducible development subsample."
    )
    parser.add_argument(
        "--target-messages",
        type=int,
        default=25000,
        help="Target number of messages in the subsample (default: 25000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/interim/development_sample.csv).",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    raw_dir = project_root / "data" / "raw"
    interim_dir = project_root / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    # Find main CSV
    csv_path = find_main_csv(raw_dir)
    if csv_path is None:
        print("Error: No CSV files found in data/raw/.")
        print("Run: python scripts/download_dataset.py")
        return 1

    print(f"Loading dataset from: {csv_path}")
    print(f"Target messages: {args.target_messages:,}")
    print(f"Random seed: {args.seed}")

    # Load data
    df = load_dataset_in_chunks(csv_path)
    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns.")

    # Identify key columns
    conversation_col = identify_conversation_column(df)
    brand_col = identify_brand_column(df)

    print(f"Conversation column: {conversation_col or 'Not found'}")
    print(f"Brand column: {brand_col or 'Not found'}")

    # Create subsample
    print("\nCreating subsample...")
    subsample, metadata = create_subsample(
        df,
        target_messages=args.target_messages,
        seed=args.seed,
        conversation_col=conversation_col,
        brand_col=brand_col,
    )

    # Save subsample
    output_path = Path(args.output) if args.output else interim_dir / "development_sample.csv"
    subsample.to_csv(output_path, index=False)
    print(f"\nSubsample saved to: {output_path}")
    print(f"Rows: {len(subsample):,}")

    # Save metadata
    metadata["source_file"] = csv_path.name
    metadata["source_rows"] = len(df)
    metadata["source_columns"] = len(df.columns)
    metadata["column_names"] = list(df.columns)
    metadata["created_at"] = datetime.now(timezone.utc).isoformat()

    metadata_path = interim_dir / "subsample_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Print summary
    print("\n--- Subsample Summary ---")
    for key, value in metadata.items():
        if key == "brand_distribution":
            print(f"  {key}:")
            for brand, count in value.items():
                print(f"    {brand}: {count}")
        else:
            print(f"  {key}: {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

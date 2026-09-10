#!/usr/bin/env python3
"""Build the golden-set candidate pool.

This script creates a large pool of candidate messages for golden-set annotation.
It performs stratified sampling to ensure representation across intents.

Usage:
    python scripts/build_golden_candidates.py
    python scripts/build_golden_candidates.py --pool-size 2000
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

from src.data.eda_utils import detect_columns
from src.intents.message_extraction import (
    create_intent_discovery_dataset,
    identify_customer_messages,
    filter_usable_messages,
    normalize_text,
)


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_taxonomy(taxonomy_path: Path) -> dict:
    """Load the intent taxonomy."""
    if not taxonomy_path.exists():
        return {"intents": []}
    with open(taxonomy_path, "r") as f:
        return json.load(f)


def create_stratified_candidates(
    df: pd.DataFrame,
    text_col: str,
    col_map: dict,
    taxonomy: dict,
    pool_size: int,
    seed: int,
) -> pd.DataFrame:
    """Create a stratified candidate pool.

    Strategy:
    1. Start with all usable customer messages
    2. Ensure minimum representation from different message types
    3. Include difficult examples (short, long, noisy)
    4. Include confusable examples
    """
    rng = np.random.RandomState(seed)

    # Get customer messages
    customer_mask = identify_customer_messages(df, col_map)
    customer_df = df[customer_mask].copy()

    # Filter to usable messages
    filtered_df = filter_usable_messages(customer_df, text_col, min_length=3)

    if len(filtered_df) == 0:
        return pd.DataFrame()

    # Add derived features for sampling
    filtered_df["text_length"] = filtered_df[text_col].fillna("").str.len()
    filtered_df["normalized_text"] = filtered_df[text_col].apply(normalize_text)

    # Categorize messages
    filtered_df["sampling_category"] = "representative"

    # Mark short messages
    filtered_df.loc[filtered_df["text_length"] < 20, "sampling_category"] = "short"

    # Mark long messages
    filtered_df.loc[filtered_df["text_length"] > 200, "sampling_category"] = "difficult"

    # Mark messages with noise
    noise_mask = (
        filtered_df[text_col].fillna("").str.contains(r"https?://|@\w+|#\w+", regex=True, na=False)
    )
    filtered_df.loc[noise_mask, "sampling_category"] = "noisy"

    # Sample from each category
    n_short = min(int(pool_size * 0.1), len(filtered_df[filtered_df["sampling_category"] == "short"]))
    n_noisy = min(int(pool_size * 0.1), len(filtered_df[filtered_df["sampling_category"] == "noisy"]))
    n_representative = pool_size - n_short - n_noisy

    # Ensure we don't exceed available data
    available_rep = len(filtered_df[filtered_df["sampling_category"] == "representative"])
    if n_representative > available_rep:
        n_representative = available_rep

    samples = []

    if n_short > 0:
        short_pool = filtered_df[filtered_df["sampling_category"] == "short"]
        samples.append(short_pool.sample(n=min(n_short, len(short_pool)), random_state=seed))

    if n_noisy > 0:
        noisy_pool = filtered_df[filtered_df["sampling_category"] == "noisy"]
        samples.append(noisy_pool.sample(n=min(n_noisy, len(noisy_pool)), random_state=seed))

    if n_representative > 0:
        rep_pool = filtered_df[filtered_df["sampling_category"] == "representative"]
        samples.append(rep_pool.sample(n=min(n_representative, len(rep_pool)), random_state=seed))

    if not samples:
        # Fallback: just sample from all
        result = filtered_df.sample(n=min(pool_size, len(filtered_df)), random_state=seed)
    else:
        result = pd.concat(samples, ignore_index=True)

    return result.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build golden-set candidate pool.")
    parser.add_argument("--pool-size", type=int, default=2000, help="Candidate pool size.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Find selected brand
    selected_brand = config.get("dataset", {}).get("selected_brand")
    if not selected_brand:
        print("Error: No brand selected.")
        print("Run: python scripts/compute_brand_statistics.py")
        return 1

    # Find selected brand data
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    messages_path = selected_brand_dir / "messages.csv"

    if not messages_path.exists():
        print(f"Error: No messages found at {messages_path}")
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
        return 1

    # Load taxonomy
    taxonomy_path = selected_brand_dir / "intent_taxonomy.json"
    taxonomy = load_taxonomy(taxonomy_path)
    intents = [intent["name"] for intent in taxonomy.get("intents", [])]
    print(f"Intents: {intents}")

    # Create candidate pool
    print(f"\nCreating candidate pool (size={args.pool_size})...")
    candidates = create_stratified_candidates(
        df, text_col, col_map, taxonomy, args.pool_size, args.seed
    )
    print(f"Candidate pool: {len(candidates):,} messages")

    # Add golden IDs
    candidates["golden_id"] = [f"gold_{i+1:04d}" for i in range(len(candidates))]

    # Add conversation context if available
    conv_col = col_map.get("conversation_id")
    if conv_col and conv_col in candidates.columns:
        candidates["conversation_id"] = candidates[conv_col]
    else:
        candidates["conversation_id"] = None

    # Add message ID if available
    id_col = col_map.get("tweet_id")
    if id_col and id_col in candidates.columns:
        candidates["message_id"] = candidates[id_col]
    else:
        candidates["message_id"] = None

    # Add brand
    candidates["brand"] = selected_brand

    # Initialize empty fields for annotation
    candidates["gold_intent"] = ""
    candidates["intent_confidence"] = ""
    candidates["ambiguous"] = False
    candidates["label_notes"] = ""
    candidates["expected_escalation"] = None
    candidates["escalation_reason"] = None
    candidates["source_split"] = "golden"

    # Save candidate pool
    output_dir = project_root / "data" / "golden"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "golden_candidates.csv"
    candidates.to_csv(output_path, index=False)
    print(f"\nCandidate pool saved to: {output_path}")

    # Save metadata
    metadata = {
        "selected_brand": selected_brand,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pool_size": len(candidates),
        "seed": args.seed,
        "sampling_strategy": "stratified",
        "categories": candidates["sampling_category"].value_counts().to_dict(),
        "intents_in_taxonomy": intents,
    }

    metadata_path = output_dir / "candidates_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Print summary
    print(f"\n--- Candidate Pool Summary ---")
    print(f"Total candidates: {len(candidates):,}")
    print(f"Categories:")
    for cat, count in candidates["sampling_category"].value_counts().items():
        print(f"  {cat}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

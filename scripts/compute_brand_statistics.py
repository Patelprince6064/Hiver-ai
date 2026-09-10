#!/usr/bin/env python3
"""Compute brand statistics and perform brand selection.

This script:
1. Loads the development dataset (or raw data).
2. Computes per-brand statistics.
3. Scores brands using the data-suitability methodology.
4. Selects the most suitable brand.
5. Saves selection results.

Usage:
    python scripts/compute_brand_statistics.py
    python scripts/compute_brand_statistics.py --input data/interim/development_sample.csv
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

from src.data.brand_selection import (
    compute_brand_features,
    score_brands,
    select_brand,
    DEFAULT_WEIGHTS,
)
from src.data.eda_utils import detect_columns


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def find_dataset(project_root: Path, input_path: str | None = None) -> Path | None:
    if input_path:
        p = Path(input_path)
        if p.exists():
            return p
        return None

    dev_sample = project_root / "data" / "interim" / "development_sample.csv"
    if dev_sample.exists():
        return dev_sample

    raw_dir = project_root / "data" / "raw"
    csv_files = sorted(raw_dir.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute brand statistics and select brand.")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()
    interim_dir = project_root / "data" / "interim"
    output_dir = Path(args.output_dir) if args.output_dir else interim_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find dataset
    dataset_path = find_dataset(project_root, args.input)
    if dataset_path is None:
        print("Error: No dataset found.")
        print("Run: python scripts/download_dataset.py")
        print("Then: python scripts/create_subsample.py --target-messages 25000 --seed 42")
        return 1

    print(f"Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path, low_memory=False)
    print(f"Loaded {len(df):,} rows.")

    # Detect columns
    col_map = detect_columns(df)
    brand_col = col_map.get("brand")
    conv_col = col_map.get("conversation_id")
    text_col = col_map.get("text")
    inbound_col = col_map.get("inbound")

    if not brand_col:
        print("Error: No brand column detected.")
        print(f"Available columns: {list(df.columns)}")
        return 1

    if not conv_col:
        print("Error: No conversation ID column detected.")
        return 1

    if not text_col:
        print("Error: No text column detected.")
        return 1

    print(f"Using columns: brand={brand_col}, conversation={conv_col}, text={text_col}, inbound={inbound_col}")

    # Compute features
    print("\nComputing brand features...")
    features = compute_brand_features(df, brand_col, conv_col, text_col, inbound_col)
    print(f"Computed features for {len(features)} brands.")

    # Score brands
    print("\nScoring brands...")
    all_scores = score_brands(features, DEFAULT_WEIGHTS)

    # Save all scores
    scores_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.name),
        "total_brands": len(all_scores),
        "weights": DEFAULT_WEIGHTS,
        "candidates": [
            {
                "rank": i + 1,
                "brand": s.brand,
                "total_score": s.total_score,
                "conversation_volume": s.conversation_volume,
                "multi_turn_coverage": s.multi_turn_coverage,
                "support_response_coverage": s.support_response_coverage,
                "conversation_quality": s.conversation_quality,
                "customer_support_density": s.customer_support_density,
                "issue_diversity_proxy": s.issue_diversity_proxy,
                "evaluation_suitability": s.evaluation_suitability,
                "raw_conversations": s.raw_conversations,
                "raw_messages": s.raw_messages,
                "raw_multi_turn_pct": s.raw_multi_turn_pct,
                "raw_response_coverage": s.raw_response_coverage,
                "raw_customer_messages": s.raw_customer_messages,
                "raw_support_messages": s.raw_support_messages,
            }
            for i, s in enumerate(all_scores[:20])
        ],
    }

    scores_path = output_dir / "brand_scores.json"
    with open(scores_path, "w") as f:
        json.dump(scores_data, f, indent=2)
    print(f"Brand scores saved to: {scores_path}")

    # Print top 10
    print("\n--- Top 10 Candidate Brands ---")
    print(f"{'Rank':<5} {'Brand':<30} {'Score':<8} {'Convs':<10} {'Multi%':<8} {'RespCov%':<10}")
    print("-" * 75)
    for i, s in enumerate(all_scores[:10]):
        print(f"{i+1:<5} {s.brand:<30} {s.total_score:<8.4f} {s.raw_conversations:<10} {s.raw_multi_turn_pct:<8.1f} {s.raw_response_coverage:<10.1f}")

    # Select brand
    min_convs = config.get("dataset", {}).get("min_conversations", 50)
    selected, _ = select_brand(df, brand_col, conv_col, text_col, inbound_col, DEFAULT_WEIGHTS, min_convs)

    if selected:
        print(f"\n--- Selected Brand ---")
        print(f"Brand: {selected.brand}")
        print(f"Total Score: {selected.total_score:.4f}")
        print(f"Conversations: {selected.raw_conversations:,}")
        print(f"Messages: {selected.raw_messages:,}")
        print(f"Multi-turn %: {selected.raw_multi_turn_pct:.1f}%")
        print(f"Response Coverage: {selected.raw_response_coverage:.1f}%")

        # Save selection
        selection = {
            "selected_brand": selected.brand,
            "selection_method": "weighted_data_suitability_score",
            "selection_timestamp": datetime.now(timezone.utc).isoformat(),
            "weights": DEFAULT_WEIGHTS,
            "total_score": selected.total_score,
            "component_scores": {
                "conversation_volume": selected.conversation_volume,
                "multi_turn_coverage": selected.multi_turn_coverage,
                "support_response_coverage": selected.support_response_coverage,
                "conversation_quality": selected.conversation_quality,
                "customer_support_density": selected.customer_support_density,
                "issue_diversity_proxy": selected.issue_diversity_proxy,
                "evaluation_suitability": selected.evaluation_suitability,
            },
            "raw_metrics": {
                "conversations": selected.raw_conversations,
                "messages": selected.raw_messages,
                "multi_turn_pct": selected.raw_multi_turn_pct,
                "response_coverage": selected.raw_response_coverage,
                "customer_messages": selected.raw_customer_messages,
                "support_messages": selected.raw_support_messages,
            },
        }

        selection_path = output_dir / "brand_selection.json"
        with open(selection_path, "w") as f:
            json.dump(selection, f, indent=2)
        print(f"Selection saved to: {selection_path}")
    else:
        print("\nNo suitable brand found.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

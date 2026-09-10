#!/usr/bin/env python3
"""Extract data for the selected brand.

This script:
1. Reads the selected brand from configs/project.yaml.
2. Loads the development dataset.
3. Filters conversations belonging to the selected brand.
4. Preserves conversation structure.
5. Saves the result under data/interim/selected_brand/.

Usage:
    python scripts/extract_selected_brand.py
    python scripts/extract_selected_brand.py --input data/interim/development_sample.csv
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

from src.data.eda_utils import detect_columns, calculate_conversation_statistics, calculate_text_statistics


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
    parser = argparse.ArgumentParser(description="Extract selected brand data.")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path.")
    parser.add_argument("--brand", type=str, default=None, help="Override brand name.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Get selected brand
    brand = args.brand or config.get("dataset", {}).get("selected_brand")
    if not brand:
        print("Error: No brand selected.")
        print("Run: python scripts/compute_brand_statistics.py")
        print("Or set selected_brand in configs/project.yaml")
        return 1

    print(f"Selected brand: {brand}")

    # Find dataset
    dataset_path = find_dataset(project_root, args.input)
    if dataset_path is None:
        print("Error: No dataset found.")
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
    time_col = col_map.get("created_at")
    id_col = col_map.get("tweet_id")

    if not brand_col:
        print("Error: No brand column detected.")
        return 1

    # Filter to selected brand
    brand_mask = df[brand_col] == brand
    brand_df = df[brand_mask].copy()

    if len(brand_df) == 0:
        print(f"Error: Brand '{brand}' not found in dataset.")
        print(f"Available brands (sample): {df[brand_col].unique()[:10].tolist()}")
        return 1

    print(f"\nFiltered to brand '{brand}': {len(brand_df):,} messages")

    # Sort by conversation and time if possible
    if conv_col and conv_col in brand_df.columns:
        sort_cols = [conv_col]
        if time_col and time_col in brand_df.columns:
            try:
                brand_df["_parsed_time"] = pd.to_datetime(brand_df[time_col], errors="coerce")
                sort_cols.append("_parsed_time")
            except Exception:
                pass

        brand_df = brand_df.sort_values(sort_cols).reset_index(drop=True)
        brand_df.drop("_parsed_time", axis=1, inplace=True, errors="ignore")

    # Create output directory
    output_dir = project_root / "data" / "interim" / "selected_brand"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save messages
    messages_path = output_dir / "messages.csv"
    brand_df.to_csv(messages_path, index=False)
    print(f"Messages saved to: {messages_path}")

    # Compute conversation-level summary
    if conv_col and conv_col in brand_df.columns:
        conv_stats = {}
        conv_groups = brand_df.groupby(conv_col)

        conversations = []
        for conv_id, group in conv_groups:
            conv_data = {
                "conversation_id": conv_id,
                "n_messages": len(group),
            }

            if text_col and text_col in group.columns:
                texts = group[text_col].fillna("").astype(str)
                conv_data["text_concatenated"] = " | ".join(texts.tolist())
                conv_data["avg_text_length"] = round(float(texts.str.len().mean()), 1)

            if inbound_col and inbound_col in group.columns:
                inbound_mask = group[inbound_col].astype(str).str.lower().isin(["true", "1", "yes"])
                conv_data["n_customer"] = int(inbound_mask.sum())
                conv_data["n_support"] = int((~inbound_mask).sum())
                conv_data["has_support_response"] = conv_data["n_support"] > 0

            conversations.append(conv_data)

        conv_df = pd.DataFrame(conversations)
        conv_path = output_dir / "conversations.csv"
        conv_df.to_csv(conv_path, index=False)
        print(f"Conversations saved to: {conv_path}")

        # Compute statistics
        conv_stats = calculate_conversation_statistics(brand_df, conv_col)

        # Response coverage
        if inbound_col and inbound_col in brand_df.columns:
            inbound_mask = brand_df[inbound_col].astype(str).str.lower().isin(["true", "1", "yes"])
            n_customer = int(inbound_mask.sum())
            n_support = int((~inbound_mask).sum())
            convs_with_support = brand_df[~inbound_mask].groupby(conv_col).ngroups
            total_convs = brand_df[conv_col].nunique()
            response_coverage = (convs_with_support / total_convs * 100) if total_convs > 0 else 0.0
        else:
            n_customer = len(brand_df) // 2
            n_support = len(brand_df) - n_customer
            response_coverage = None

        # Text stats
        text_stats = {}
        if text_col and text_col in brand_df.columns:
            text_stats = calculate_text_statistics(brand_df[text_col], label=brand)

        stats = {
            "brand": brand,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_messages": len(brand_df),
            "total_conversations": brand_df[conv_col].nunique() if conv_col in brand_df.columns else None,
            "customer_messages": n_customer,
            "support_messages": n_support,
            "response_coverage": round(response_coverage, 2) if response_coverage is not None else None,
            "conversation_statistics": conv_stats,
            "text_statistics": text_stats,
        }

        stats_path = output_dir / "statistics.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Statistics saved to: {stats_path}")

        # Print summary
        print(f"\n--- Selected Brand Summary ---")
        print(f"Brand: {brand}")
        print(f"Messages: {stats['total_messages']:,}")
        print(f"Conversations: {stats['total_conversations']:,}")
        print(f"Customer messages: {stats['customer_messages']:,}")
        print(f"Support messages: {stats['support_messages']:,}")
        if response_coverage is not None:
            print(f"Response coverage: {stats['response_coverage']:.1f}%")
        print(f"Median conversation length: {conv_stats.get('median_length', 'N/A')}")
    else:
        print("Warning: No conversation ID column. Cannot compute conversation-level statistics.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

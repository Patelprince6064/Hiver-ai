#!/usr/bin/env python3
"""Check for data leakage between golden set and development data.

This script checks:
- Conversation overlap
- Message ID overlap
- Exact text overlap

Usage:
    python scripts/check_golden_leakage.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.golden_schema import load_golden_set


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()

    # Find golden set
    golden_path = project_root / "data" / "golden" / "golden_set.jsonl"
    if not golden_path.exists():
        print("Error: No golden set found.")
        return 1

    # Load golden set
    golden_examples = load_golden_set(golden_path)
    print(f"Loaded {len(golden_examples)} golden examples.")

    # Load development sample
    dev_path = project_root / config["dataset"]["development_sample"]
    if not dev_path.exists():
        print("Warning: No development sample found. Skipping overlap checks.")
        dev_df = None
    else:
        dev_df = pd.read_csv(dev_path, low_memory=False)
        print(f"Loaded {len(dev_df):,} development messages.")

    # Load selected brand data
    selected_brand_dir = project_root / config["dataset"]["selected_brand_dir"]
    brand_messages_path = selected_brand_dir / "messages.csv"
    if brand_messages_path.exists():
        brand_df = pd.read_csv(brand_messages_path, low_memory=False)
        print(f"Loaded {len(brand_df):,} selected-brand messages.")
    else:
        brand_df = None

    # Collect golden set identifiers
    golden_conversation_ids = set(
        e.get("conversation_id") for e in golden_examples if e.get("conversation_id")
    )
    golden_message_ids = set(
        e.get("message_id") for e in golden_examples if e.get("message_id")
    )
    golden_texts = set(
        e.get("customer_message", "").strip().lower() for e in golden_examples
    )

    print(f"\nGolden set identifiers:")
    print(f"  Conversation IDs: {len(golden_conversation_ids)}")
    print(f"  Message IDs: {len(golden_message_ids)}")
    print(f"  Unique texts: {len(golden_texts)}")

    # Check overlap with development sample
    leakage_report = {
        "conversation_overlap": 0,
        "message_id_overlap": 0,
        "text_overlap": 0,
        "total_golden": len(golden_examples),
        "details": [],
    }

    if dev_df is not None:
        # Check conversation overlap
        if "conversation_id" in dev_df.columns:
            dev_conv_ids = set(dev_df["conversation_id"].dropna().unique())
            conv_overlap = golden_conversation_ids & dev_conv_ids
            leakage_report["conversation_overlap"] = len(conv_overlap)
            if conv_overlap:
                leakage_report["details"].append(
                    f"Conversation ID overlap: {len(conv_overlap)} conversations"
                )

        # Check message ID overlap
        for id_col in ["tweet_id", "message_id"]:
            if id_col in dev_df.columns:
                dev_msg_ids = set(dev_df[id_col].dropna().unique())
                msg_overlap = golden_message_ids & dev_msg_ids
                leakage_report["message_id_overlap"] = max(
                    leakage_report["message_id_overlap"], len(msg_overlap)
                )
                if msg_overlap:
                    leakage_report["details"].append(
                        f"Message ID overlap ({id_col}): {len(msg_overlap)} messages"
                    )

        # Check text overlap
        if "text" in dev_df.columns:
            dev_texts = set(dev_df["text"].fillna("").str.strip().str.lower().unique())
            text_overlap = golden_texts & dev_texts
            leakage_report["text_overlap"] = len(text_overlap)
            if text_overlap:
                leakage_report["details"].append(
                    f"Exact text overlap: {len(text_overlap)} messages"
                )

    # Check overlap with selected brand data
    if brand_df is not None:
        if "conversation_id" in brand_df.columns:
            brand_conv_ids = set(brand_df["conversation_id"].dropna().unique())
            conv_overlap = golden_conversation_ids & brand_conv_ids
            if conv_overlap:
                leakage_report["details"].append(
                    f"Conversation overlap with brand data: {len(conv_overlap)} (expected - golden is subset)"
                )

    # Print report
    print("\n" + "=" * 70)
    print("DATA LEAKAGE REPORT")
    print("=" * 70)

    has_leakage = False
    if leakage_report["conversation_overlap"] > 0:
        print(f"\n✗ Conversation ID overlap: {leakage_report['conversation_overlap']}")
        has_leakage = True
    else:
        print(f"\n✓ No conversation ID overlap")

    if leakage_report["message_id_overlap"] > 0:
        print(f"✗ Message ID overlap: {leakage_report['message_id_overlap']}")
        has_leakage = True
    else:
        print(f"✓ No message ID overlap")

    if leakage_report["text_overlap"] > 0:
        print(f"✗ Exact text overlap: {leakage_report['text_overlap']}")
        has_leakage = True
    else:
        print(f"✓ No exact text overlap")

    if leakage_report["details"]:
        print(f"\nDetails:")
        for detail in leakage_report["details"]:
            print(f"  - {detail}")

    if not has_leakage:
        print(f"\n✓ No data leakage detected.")
    else:
        print(f"\n⚠ Data leakage detected. Review before proceeding.")

    # Save report
    report_path = project_root / "data" / "golden" / "leakage_report.json"
    with open(report_path, "w") as f:
        json.dump(leakage_report, f, indent=2)
    print(f"\nReport saved to: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

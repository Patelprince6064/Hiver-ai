#!/usr/bin/env python3
"""Check for data leakage between retrieval index and golden set.

Usage:
    python scripts/check_retrieval_index_leakage.py
"""

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import load_golden_data


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()
    retrieval_config = config.get("retrieval", {})

    # Load index records
    index_dir = project_root / retrieval_config.get("index", {}).get("save_dir", "data/processed/retrieval_index")
    records_path = index_dir / "records.jsonl"

    if not records_path.exists():
        print("Error: Index records not found.")
        print("Run: python scripts/build_retrieval_index.py")
        return 1

    kb_records = []
    with open(records_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                kb_records.append(json.loads(line))

    print(f"Retrieval index: {len(kb_records):,} records")

    # Load golden set
    try:
        golden_df = load_golden_data()
        print(f"Golden set: {len(golden_df):,} examples")
    except FileNotFoundError:
        print("Golden set not found. Skipping leakage check.")
        return 0

    # Extract identifiers
    kb_conversation_ids = set(
        r.get("conversation_id") for r in kb_records if r.get("conversation_id")
    )
    golden_conversation_ids = set(
        golden_df["conversation_id"].dropna().unique()
    ) if "conversation_id" in golden_df.columns else set()

    kb_customer_messages = set(
        r.get("customer_message", "").strip().lower() for r in kb_records
    )
    golden_customer_messages = set(
        golden_df["text"].fillna("").str.strip().str.lower().unique()
    ) if "text" in golden_df.columns else set()

    kb_support_responses = set(
        r.get("support_response", "").strip().lower() for r in kb_records
    )

    # Check overlaps
    conv_overlap = kb_conversation_ids & golden_conversation_ids
    msg_overlap = kb_customer_messages & golden_customer_messages

    # Print report
    print(f"\n{'='*70}")
    print("RETRIEVAL INDEX LEAKAGE CHECK")
    print(f"{'='*70}")

    has_leakage = False

    if conv_overlap:
        print(f"\n✗ Conversation ID overlap: {len(conv_overlap)}")
        has_leakage = True
    else:
        print(f"\n✓ No conversation ID overlap")

    if msg_overlap:
        print(f"✗ Exact text overlap: {len(msg_overlap)}")
        has_leakage = True
    else:
        print(f"✓ No exact text overlap")

    # Save report
    report = {
        "has_leakage": has_leakage,
        "conversation_overlap": len(conv_overlap),
        "text_overlap": len(msg_overlap),
    }

    report_path = project_root / "evaluation" / "results" / "retrieval_index_leakage_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    if has_leakage:
        print(f"\n✗ LEAKAGE DETECTED")
        return 1
    else:
        print(f"\n✓ NO LEAKAGE DETECTED")
        return 0


if __name__ == "__main__":
    sys.exit(main())

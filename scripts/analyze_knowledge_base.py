#!/usr/bin/env python3
"""Analyze knowledge base statistics.

Usage:
    python scripts/analyze_knowledge_base.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    project_root = find_project_root()

    # Load knowledge base
    kb_path = project_root / "data" / "processed" / "knowledge_base.jsonl"
    if not kb_path.exists():
        print("Error: Knowledge base not found.")
        print("Run: python scripts/build_knowledge_base.py")
        return 1

    records = []
    with open(kb_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records):,} knowledge records")

    df = pd.DataFrame(records)

    # Statistics
    stats = {
        "total_records": len(records),
        "unique_conversations": df["conversation_id"].nunique() if "conversation_id" in df.columns else 0,
        "unique_customer_messages": df["customer_message"].nunique() if "customer_message" in df.columns else 0,
        "unique_support_responses": df["support_response"].nunique() if "support_response" in df.columns else 0,
    }

    # Records per intent
    if "intent" in df.columns:
        stats["records_per_intent"] = df["intent"].value_counts().to_dict()
    else:
        stats["records_per_intent"] = {}

    # Records per resolution type
    if "resolution_type" in df.columns:
        stats["records_per_resolution"] = df["resolution_type"].value_counts().to_dict()
    else:
        stats["records_per_resolution"] = {}

    # Average lengths
    if "customer_message" in df.columns:
        stats["avg_customer_message_length"] = float(df["customer_message"].str.len().mean())
    if "support_response" in df.columns:
        stats["avg_support_response_length"] = float(df["support_response"].str.len().mean())

    # Context availability
    if "resolution_text" in df.columns:
        stats["has_context"] = int(df["resolution_text"].str.contains("context", na=False).sum())

    # Follow-up availability
    if "has_followup" in df.columns:
        stats["has_followup"] = int(df["has_followup"].sum())

    # Quality categories
    if "quality_category" in df.columns:
        stats["quality_distribution"] = df["quality_category"].value_counts().to_dict()
    else:
        stats["quality_distribution"] = {}

    # Save statistics
    stats_path = project_root / "data" / "processed" / "knowledge_base_statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nStatistics saved to: {stats_path}")

    # Print summary
    print(f"\n--- Knowledge Base Statistics ---")
    print(f"Total records: {stats['total_records']:,}")
    print(f"Unique conversations: {stats['unique_conversations']:,}")
    print(f"Unique customer messages: {stats['unique_customer_messages']:,}")
    print(f"Unique support responses: {stats['unique_support_responses']:,}")

    print(f"\nRecords per intent:")
    for intent, count in sorted(stats["records_per_intent"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {intent}: {count}")

    print(f"\nRecords per resolution type:")
    for res, count in sorted(stats["records_per_resolution"].items(), key=lambda x: -x[1]):
        print(f"  {res}: {count}")

    print(f"\nQuality distribution:")
    for cat, count in stats["quality_distribution"].items():
        print(f"  {cat}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

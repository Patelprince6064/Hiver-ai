#!/usr/bin/env python3
"""Verify split isolation between train/dev/test and golden set.

Checks for data leakage at conversation, message, and text level.

Usage:
    python scripts/verify_split_isolation.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import (
    load_dev_data,
    load_golden_data,
    load_test_data,
    load_train_data,
)


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def check_overlap(
    split_a: pd.DataFrame,
    split_b: pd.DataFrame,
    name_a: str,
    name_b: str,
) -> dict:
    """Check for overlap between two splits."""
    report = {
        "pair": f"{name_a} vs {name_b}",
        "conversation_overlap": 0,
        "message_overlap": 0,
        "text_overlap": 0,
        "has_leakage": False,
    }

    # Conversation ID overlap
    if "conversation_id" in split_a.columns and "conversation_id" in split_b.columns:
        conv_a = set(split_a["conversation_id"].dropna().unique())
        conv_b = set(split_b["conversation_id"].dropna().unique())
        report["conversation_overlap"] = len(conv_a & conv_b)

    # Message ID overlap
    for id_col in ["tweet_id", "message_id"]:
        if id_col in split_a.columns and id_col in split_b.columns:
            ids_a = set(split_a[id_col].dropna().unique())
            ids_b = set(split_b[id_col].dropna().unique())
            report["message_overlap"] = max(report["message_overlap"], len(ids_a & ids_b))

    # Text overlap
    if "text" in split_a.columns and "text" in split_b.columns:
        texts_a = set(split_a["text"].fillna("").str.strip().str.lower().unique())
        texts_b = set(split_b["text"].fillna("").str.strip().str.lower().unique())
        report["text_overlap"] = len(texts_a & texts_b)

    report["has_leakage"] = any(v > 0 for k, v in report.items() if k.endswith("_overlap"))
    return report


def main() -> int:
    project_root = find_project_root()

    # Load splits
    try:
        train_df = load_train_data()
        dev_df = load_dev_data()
        test_df = load_test_data()
        golden_df = load_golden_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    print(f"Train: {len(train_df):,}")
    print(f"Dev: {len(dev_df):,}")
    print(f"Test: {len(test_df):,}")
    print(f"Golden: {len(golden_df):,}")

    # Check overlaps
    checks = [
        (train_df, golden_df, "train", "golden"),
        (dev_df, golden_df, "dev", "golden"),
        (test_df, golden_df, "test", "golden"),
    ]

    reports = []
    has_leakage = False

    print("\n" + "=" * 70)
    print("SPLIT ISOLATION VERIFICATION")
    print("=" * 70)

    for split_a, split_b, name_a, name_b in checks:
        report = check_overlap(split_a, split_b, name_a, name_b)
        reports.append(report)

        status = "✗ LEAKAGE" if report["has_leakage"] else "✓ CLEAN"
        print(f"\n{report['pair']}: {status}")
        print(f"  Conversation overlap: {report['conversation_overlap']}")
        print(f"  Message overlap: {report['message_overlap']}")
        print(f"  Text overlap: {report['text_overlap']}")

        if report["has_leakage"]:
            has_leakage = True

    print("\n" + "=" * 70)
    if has_leakage:
        print("RESULT: DATA LEAKAGE DETECTED")
        print("Fix leakage before proceeding.")
    else:
        print("RESULT: NO DATA LEAKAGE")
        print("All splits are isolated from golden set.")

    # Save report
    output_path = project_root / "evaluation" / "results"
    output_path.mkdir(parents=True, exist_ok=True)

    report_data = {
        "has_leakage": has_leakage,
        "checks": reports,
    }

    with open(output_path / "split_isolation_report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    return 1 if has_leakage else 0


if __name__ == "__main__":
    sys.exit(main())

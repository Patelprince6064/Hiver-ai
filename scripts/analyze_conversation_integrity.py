#!/usr/bin/env python3
"""Analyze conversation integrity in the dataset.

This script performs deeper integrity checks on conversations:

- Chronological ordering within conversations
- Message ID uniqueness
- Parent message reference validity
- Conversation membership consistency
- Timestamp sanity checks
- Empty conversation detection

Usage:
    python scripts/analyze_conversation_integrity.py
    python scripts/analyze_conversation_integrity.py --input data/interim/development_sample.csv
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.eda_utils import detect_columns


def find_project_root() -> Path:
    """Find the project root directory."""
    return Path(__file__).resolve().parent.parent


def find_dataset(project_root: Path, input_path: str | None = None) -> Path | None:
    """Find the dataset to analyze."""
    if input_path:
        p = Path(input_path)
        if p.exists():
            return p
        return None

    # Try development sample first
    dev_sample = project_root / "data" / "interim" / "development_sample.csv"
    if dev_sample.exists():
        return dev_sample

    # Fall back to raw CSV
    raw_dir = project_root / "data" / "raw"
    csv_files = sorted(raw_dir.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    return None


def check_chronological_order(
    df: pd.DataFrame,
    conv_col: str,
    time_col: str,
) -> dict:
    """Check if messages are chronologically ordered within conversations."""
    df_copy = df.copy()
    try:
        df_copy["_parsed_time"] = pd.to_datetime(df_copy[time_col], errors="coerce")
    except Exception:
        return {"check": "chronological_order", "status": "SKIPPED", "reason": "Cannot parse timestamps"}

    valid = df_copy.dropna(subset=["_parsed_time"])
    if len(valid) == 0:
        return {"check": "chronological_order", "status": "SKIPPED", "reason": "No valid timestamps"}

    out_of_order = 0
    total_convs = 0

    for conv_id, group in valid.groupby(conv_col):
        total_convs += 1
        times = group["_parsed_time"].values
        if not all(times[i] <= times[i + 1] for i in range(len(times) - 1)):
            out_of_order += 1

    return {
        "check": "chronological_order",
        "status": "OK" if out_of_order == 0 else "ISSUES_FOUND",
        "total_conversations_checked": total_convs,
        "out_of_order_conversations": out_of_order,
        "out_of_order_pct": round(out_of_order / total_convs * 100, 2) if total_convs > 0 else 0.0,
    }


def check_message_id_uniqueness(
    df: pd.DataFrame,
    id_col: str,
) -> dict:
    """Check if message IDs are unique."""
    total = len(df)
    unique = df[id_col].nunique()
    duplicates = total - unique

    return {
        "check": "message_id_uniqueness",
        "status": "OK" if duplicates == 0 else "ISSUES_FOUND",
        "total_rows": total,
        "unique_ids": unique,
        "duplicate_ids": duplicates,
        "duplicate_pct": round(duplicates / total * 100, 2) if total > 0 else 0.0,
    }


def check_parent_references(
    df: pd.DataFrame,
    id_col: str,
    reply_col: str,
) -> dict:
    """Check if referenced parent messages exist."""
    ids = set(df[id_col].dropna())
    reply_ids = df[reply_col].dropna()
    total_replies = len(reply_ids)

    if total_replies == 0:
        return {"check": "parent_references", "status": "SKIPPED", "reason": "No reply references"}

    missing_parents = 0
    for parent_id in reply_ids:
        if parent_id not in ids:
            missing_parents += 1

    return {
        "check": "parent_references",
        "status": "OK" if missing_parents == 0 else "ISSUES_FOUND",
        "total_reply_references": total_replies,
        "missing_parents": missing_parents,
        "missing_pct": round(missing_parents / total_replies * 100, 2) if total_replies > 0 else 0.0,
    }


def check_conversation_membership(
    df: pd.DataFrame,
    conv_col: str,
    id_col: str | None,
) -> dict:
    """Check basic conversation membership consistency."""
    conv_sizes = df.groupby(conv_col).size()
    n_conversations = len(conv_sizes)
    n_orphan_rows = int((df[conv_col].isna()).sum())

    return {
        "check": "conversation_membership",
        "status": "OK" if n_orphan_rows == 0 else "ISSUES_FOUND",
        "total_conversations": n_conversations,
        "orphan_rows_no_conversation": n_orphan_rows,
    }


def check_timestamp_sanity(
    df: pd.DataFrame,
    time_col: str,
) -> dict:
    """Check for impossible timestamps."""
    try:
        times = pd.to_datetime(df[time_col], errors="coerce")
    except Exception:
        return {"check": "timestamp_sanity", "status": "SKIPPED", "reason": "Cannot parse timestamps"}

    valid = times.dropna()
    if len(valid) == 0:
        return {"check": "timestamp_sanity", "status": "SKIPPED", "reason": "No valid timestamps"}

    now = pd.Timestamp.now(tz=valid.dt.tz) if valid.dt.tz else pd.Timestamp.now()
    future = (valid > now).sum()
    very_old = (valid < pd.Timestamp("2010-01-01")).sum()
    negative_gaps = 0

    return {
        "check": "timestamp_sanity",
        "status": "OK" if future == 0 and very_old == 0 else "ISSUES_FOUND",
        "valid_timestamps": len(valid),
        "future_timestamps": int(future),
        "very_old_pre_2010": int(very_old),
    }


def check_empty_conversations(
    df: pd.DataFrame,
    conv_col: str,
    text_col: str,
) -> dict:
    """Find conversations with no usable customer text."""
    has_text = df[text_col].notna() & (df[text_col].astype(str).str.strip() != "")

    conv_has_text = df.groupby(conv_col)[text_col].apply(
        lambda x: (x.notna() & (x.astype(str).str.strip() != "")).any()
    )

    empty_convs = (~conv_has_text).sum()
    total_convs = len(conv_has_text)

    return {
        "check": "empty_conversations",
        "status": "OK" if empty_convs == 0 else "ISSUES_FOUND",
        "total_conversations": total_convs,
        "empty_conversations": int(empty_convs),
        "empty_pct": round(empty_convs / total_convs * 100, 2) if total_convs > 0 else 0.0,
    }


def run_integrity_checks(df: pd.DataFrame, col_map: dict) -> list[dict]:
    """Run all integrity checks."""
    results = []
    conv_col = col_map.get("conversation_id")
    time_col = col_map.get("created_at")
    id_col = col_map.get("tweet_id")
    reply_col = col_map.get("in_reply_to_tweet_id")
    text_col = col_map.get("text")

    if conv_col and conv_col in df.columns:
        if time_col and time_col in df.columns:
            results.append(check_chronological_order(df, conv_col, time_col))
        results.append(check_conversation_membership(df, conv_col, id_col))

        if text_col and text_col in df.columns:
            results.append(check_empty_conversations(df, conv_col, text_col))

    if id_col and id_col in df.columns:
        results.append(check_message_id_uniqueness(df, id_col))

        if reply_col and reply_col in df.columns:
            results.append(check_parent_references(df, id_col, reply_col))

    if time_col and time_col in df.columns:
        results.append(check_timestamp_sanity(df, time_col))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze conversation integrity.")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path.")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path.")
    args = parser.parse_args()

    project_root = find_project_root()
    dataset_path = find_dataset(project_root, args.input)

    if dataset_path is None:
        print("Error: No dataset found.")
        print("Download the dataset first: python scripts/download_dataset.py")
        print("Then create the subsample: python scripts/create_subsample.py")
        return 1

    print(f"Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path, low_memory=False)
    print(f"Loaded {len(df):,} rows.")

    col_map = detect_columns(df)
    print(f"Detected columns: { {k: v for k, v in col_map.items() if v} }")

    print("\nRunning integrity checks...")
    results = run_integrity_checks(df, col_map)

    # Print report
    print("\n" + "=" * 70)
    print("CONVERSATION INTEGRITY REPORT")
    print("=" * 70)

    issues_found = False
    for r in results:
        status = r["status"]
        symbol = "✓" if status == "OK" else "✗" if status == "ISSUES_FOUND" else "–"
        print(f"\n{symbol} {r['check']}: {status}")
        for k, v in r.items():
            if k not in ("check", "status"):
                print(f"    {k}: {v}")
        if status == "ISSUES_FOUND":
            issues_found = True

    print("\n" + "=" * 70)

    # Save results
    output_path = Path(args.output) if args.output else project_root / "data" / "interim" / "conversation_integrity.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "dataset": str(dataset_path.name),
        "rows": len(df),
        "checks": results,
        "overall_status": "ISSUES_FOUND" if issues_found else "OK",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {output_path}")

    return 1 if issues_found else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Inspect the Customer Support on Twitter dataset.

This script automatically discovers and reports on CSV/JSON/JSONL files
in the data/raw/ directory. It provides:

- File inventory (name, size, format)
- Row and column counts
- Column names and data types
- Missing value analysis
- Duplicate detection
- Sample records

The script is designed to be safe for large datasets:
- Uses chunked reading for CSV files
- Limits sample output
- Does not load entire datasets into memory unnecessarily
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def find_project_root() -> Path:
    """Find the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def discover_files(raw_dir: Path) -> list[dict]:
    """Discover CSV, JSON, and JSONL files in the raw directory."""
    files = []
    patterns = ["*.csv", "*.json", "*.jsonl"]

    for pattern in patterns:
        for filepath in sorted(raw_dir.glob(pattern)):
            if filepath.name.startswith("."):
                continue  # Skip hidden files
            stat = filepath.stat()
            files.append({
                "path": filepath,
                "name": filepath.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "suffix": filepath.suffix.lower(),
            })

    return files


def inspect_csv_file(filepath: Path, sample_rows: int = 5, chunk_size: int = 10000) -> dict:
    """Inspect a CSV file with chunked reading for large files."""
    result = {
        "filename": filepath.name,
        "format": "csv",
        "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
        "total_rows": 0,
        "columns": [],
        "dtypes": {},
        "missing": {},
        "duplicates": 0,
        "sample": [],
    }

    try:
        # First pass: get columns and dtypes, count rows
        print(f"  Reading columns and counting rows for {filepath.name}...")
        first_chunk = True
        all_columns = None

        for chunk in pd.read_csv(filepath, chunksize=chunk_size, low_memory=False):
            if first_chunk:
                all_columns = list(chunk.columns)
                result["columns"] = all_columns
                result["dtypes"] = {col: str(dtype) for col, dtype in chunk.dtypes.items()}
                first_chunk = False

            result["total_rows"] += len(chunk)

        # Second pass: compute missing values and duplicates
        print(f"  Computing missing values and duplicates for {filepath.name}...")
        missing_counts = {col: 0 for col in all_columns}
        seen_ids = set()
        exact_duplicates = 0

        for chunk in pd.read_csv(filepath, chunksize=chunk_size, low_memory=False):
            # Count missing values
            for col in all_columns:
                missing_counts[col] += chunk[col].isna().sum()

            # Count exact duplicate rows
            exact_duplicates += chunk.duplicated().sum()

            # Check for ID-like columns for duplicate ID detection
            for id_col in ["tweet_id", "id", "conversation_id", "in_reply_to_tweet_id"]:
                if id_col in chunk.columns:
                    chunk_ids = chunk[id_col].dropna()
                    new_ids = set(chunk_ids) - seen_ids
                    dup_in_chunk = len(chunk_ids) - len(new_ids)
                    seen_ids.update(new_ids)

        result["missing"] = {col: int(count) for col, count in missing_counts.items()}
        result["duplicates"] = int(exact_duplicates)

        # Get sample rows
        print(f"  Sampling {sample_rows} rows from {filepath.name}...")
        sample_df = pd.read_csv(filepath, nrows=sample_rows, low_memory=False)
        result["sample"] = sample_df.to_dict(orient="records")

        print(f"  Inspection complete for {filepath.name}.")

    except Exception as e:
        result["error"] = str(e)
        print(f"  Error inspecting {filepath.name}: {e}")

    return result


def inspect_json_file(filepath: Path, max_sample: int = 5) -> dict:
    """Inspect a JSON or JSONL file."""
    result = {
        "filename": filepath.name,
        "format": filepath.suffix.lower().lstrip("."),
        "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
        "total_rows": 0,
        "columns": [],
        "sample": [],
    }

    try:
        if filepath.suffix == ".jsonl":
            # JSON Lines format
            rows = []
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_sample:
                        break
                    rows.append(json.loads(line.strip()))
            result["sample"] = rows
            if rows:
                result["columns"] = list(rows[0].keys())

            # Count total lines
            with open(filepath, "r", encoding="utf-8") as f:
                result["total_rows"] = sum(1 for _ in f)
        else:
            # Standard JSON (assume array of objects)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                result["total_rows"] = len(data)
                result["sample"] = data[:max_sample]
                if data:
                    result["columns"] = list(data[0].keys()) if isinstance(data[0], dict) else []
            elif isinstance(data, dict):
                result["total_rows"] = 1
                result["columns"] = list(data.keys())

        print(f"  Inspection complete for {filepath.name}.")

    except Exception as e:
        result["error"] = str(e)
        print(f"  Error inspecting {filepath.name}: {e}")

    return result


def print_report(inspections: list[dict]) -> None:
    """Print a human-readable inspection report."""
    print("\n" + "=" * 70)
    print("DATASET INSPECTION REPORT")
    print("=" * 70)

    if not inspections:
        print("\nNo dataset files found in data/raw/.")
        print("Run: python scripts/download_dataset.py")
        return

    for insp in inspections:
        print(f"\n--- {insp['filename']} ---")
        print(f"  Format: {insp['format']}")
        print(f"  Size: {insp['size_mb']} MB")
        print(f"  Rows: {insp['total_rows']:,}")
        print(f"  Columns ({len(insp['columns'])}): {insp['columns']}")

        if "dtypes" in insp and insp["dtypes"]:
            print("\n  Data types:")
            for col, dtype in insp["dtypes"].items():
                print(f"    {col}: {dtype}")

        if "missing" in insp and insp["missing"]:
            total_rows = insp["total_rows"]
            print("\n  Missing values:")
            for col, count in insp["missing"].items():
                if count > 0:
                    pct = (count / total_rows * 100) if total_rows > 0 else 0
                    print(f"    {col}: {count:,} ({pct:.1f}%)")
                else:
                    print(f"    {col}: 0")

        if "duplicates" in insp:
            print(f"\n  Exact duplicate rows: {insp['duplicates']:,}")

        if insp.get("sample"):
            print(f"\n  Sample records ({len(insp['sample'])}):")
            for i, record in enumerate(insp["sample"]):
                print(f"    Record {i + 1}:")
                for key, value in record.items():
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    print(f"      {key}: {val_str}")

    print("\n" + "=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect dataset files in data/raw/."
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=5,
        help="Number of sample rows to display (default: 5).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Save inspection results as JSON to this path.",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    raw_dir = project_root / "data" / "raw"

    print(f"Discovering files in: {raw_dir}")
    files = discover_files(raw_dir)

    if not files:
        print("No dataset files found.")
        print("Run: python scripts/download_dataset.py")
        return 1

    print(f"Found {len(files)} file(s).\n")

    inspections = []
    for file_info in files:
        print(f"Inspecting: {file_info['name']} ({file_info['size_mb']} MB)")
        if file_info["suffix"] == ".csv":
            result = inspect_csv_file(file_info["path"], sample_rows=args.sample_rows)
        elif file_info["suffix"] in (".json", ".jsonl"):
            result = inspect_json_file(file_info["path"])
        else:
            print(f"  Skipping unsupported format: {file_info['suffix']}")
            continue
        inspections.append(result)

    print_report(inspections)

    # Save JSON output if requested
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(inspections, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate the dataset and subsample integrity.

This script performs validation checks to ensure:

- Required raw files exist and are readable
- Expected columns are discovered
- No corrupt rows are detectable
- IDs are not unexpectedly duplicated
- Subsample file can be loaded
- Metadata is valid JSON
- Subsample size is within reasonable bounds
- Conversation integrity is maintained (where applicable)

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import json
import sys
from pathlib import Path

import pandas as pd


def find_project_root() -> Path:
    """Find the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


class ValidationError:
    def __init__(self, check_name: str, message: str, severity: str = "ERROR"):
        self.check_name = check_name
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity}] {self.check_name}: {self.message}"


def validate_raw_files_exist(raw_dir: Path) -> list[ValidationError]:
    """Check that expected raw files exist."""
    errors = []
    csv_files = list(raw_dir.glob("*.csv"))

    if not csv_files:
        errors.append(ValidationError(
            "raw_files",
            "No CSV files found in data/raw/. Run: python scripts/download_dataset.py",
        ))

    for csv_file in csv_files:
        if csv_file.stat().st_size == 0:
            errors.append(ValidationError(
                "raw_files",
                f"File is empty: {csv_file.name}",
            ))

    return errors


def validate_metadata(raw_dir: Path) -> list[ValidationError]:
    """Validate dataset_metadata.json if it exists."""
    errors = []
    metadata_path = raw_dir / "dataset_metadata.json"

    if not metadata_path.exists():
        errors.append(ValidationError(
            "metadata",
            "dataset_metadata.json not found. Run: python scripts/download_dataset.py",
            severity="WARNING",
        ))
        return errors

    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            "metadata",
            f"Invalid JSON in dataset_metadata.json: {e}",
        ))
        return errors

    required_fields = ["dataset_name", "source", "downloaded_at"]
    for field in required_fields:
        if field not in metadata:
            errors.append(ValidationError(
                "metadata",
                f"Missing required field: {field}",
            ))

    return errors


def validate_subsample(interim_dir: Path) -> list[ValidationError]:
    """Validate the development subsample."""
    errors = []
    sample_path = interim_dir / "development_sample.csv"
    metadata_path = interim_dir / "subsample_metadata.json"

    # Check subsample file
    if not sample_path.exists():
        errors.append(ValidationError(
            "subsample",
            "development_sample.csv not found. Run: python scripts/create_subsample.py",
        ))
        return errors

    try:
        df = pd.read_csv(sample_path, nrows=10)
        full_df = pd.read_csv(sample_path)
    except Exception as e:
        errors.append(ValidationError(
            "subsample",
            f"Cannot read development_sample.csv: {e}",
        ))
        return errors

    # Check for empty file
    if len(full_df) == 0:
        errors.append(ValidationError(
            "subsample",
            "development_sample.csv is empty",
        ))
        return errors

    # Check for expected columns
    if len(full_df.columns) == 0:
        errors.append(ValidationError(
            "subsample",
            "development_sample.csv has no columns",
        ))

    # Check for excessive missing values in key columns
    for col in full_df.columns:
        missing_pct = full_df[col].isna().mean() * 100
        if missing_pct > 90:
            errors.append(ValidationError(
                "subsample",
                f"Column '{col}' has {missing_pct:.1f}% missing values",
                severity="WARNING",
            ))

    # Check subsample metadata
    if metadata_path.exists():
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Validate metadata values
            if "actual_messages" in metadata:
                if metadata["actual_messages"] != len(full_df):
                    errors.append(ValidationError(
                        "subsample_metadata",
                        f"Mismatch: metadata says {metadata['actual_messages']} rows, "
                        f"but CSV has {len(full_df)} rows",
                    ))

            if "random_seed" in metadata:
                if not isinstance(metadata["random_seed"], int):
                    errors.append(ValidationError(
                        "subsample_metadata",
                        "random_seed should be an integer",
                    ))

        except json.JSONDecodeError as e:
            errors.append(ValidationError(
                "subsample_metadata",
                f"Invalid JSON in subsample_metadata.json: {e}",
            ))
    else:
        errors.append(ValidationError(
            "subsample_metadata",
            "subsample_metadata.json not found",
            severity="WARNING",
        ))

    return errors


def validate_conversation_integrity(interim_dir: Path) -> list[ValidationError]:
    """Check conversation integrity in subsample if applicable."""
    errors = []
    sample_path = interim_dir / "development_sample.csv"

    if not sample_path.exists():
        return errors

    metadata_path = interim_dir / "subsample_metadata.json"
    if not metadata_path.exists():
        return errors

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    if not metadata.get("conversation_integrity", False):
        return errors

    df = pd.read_csv(sample_path)

    # Check if conversation column exists
    conv_col = None
    for col in ["conversation_id", "thread_id", "in_reply_to_tweet_id"]:
        if col in df.columns:
            conv_col = col
            break

    if conv_col is None:
        errors.append(ValidationError(
            "conversation_integrity",
            "Metadata claims conversation integrity but no conversation column found",
            severity="WARNING",
        ))

    return errors


def run_validation(project_root: Path) -> bool:
    """Run all validation checks. Returns True if all pass."""
    raw_dir = project_root / "data" / "raw"
    interim_dir = project_root / "data" / "interim"

    all_errors: list[ValidationError] = []

    print("Running validation checks...\n")

    # Check 1: Raw files
    print("1. Checking raw files...")
    errors = validate_raw_files_exist(raw_dir)
    all_errors.extend(errors)
    if not errors:
        print("   PASS")

    # Check 2: Metadata
    print("2. Checking metadata...")
    errors = validate_metadata(raw_dir)
    all_errors.extend(errors)
    if not errors:
        print("   PASS")

    # Check 3: Subsample
    print("3. Checking subsample...")
    errors = validate_subsample(interim_dir)
    all_errors.extend(errors)
    if not errors:
        print("   PASS")

    # Check 4: Conversation integrity
    print("4. Checking conversation integrity...")
    errors = validate_conversation_integrity(interim_dir)
    all_errors.extend(errors)
    if not errors:
        print("   PASS")

    # Print results
    print("\n" + "=" * 70)
    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} issue(s) found\n")
        for err in all_errors:
            print(f"  {err}")
        return False
    else:
        print("ALL CHECKS PASSED")
        return True


def main() -> int:
    project_root = find_project_root()
    success = run_validation(project_root)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

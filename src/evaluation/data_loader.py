"""Evaluation data loader.

Provides functions for loading train/dev/test/golden data with schema validation.
Clearly distinguishes development data from locked golden evaluation data.
"""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_split_dir() -> Path:
    return PROJECT_ROOT / "data" / "processed" / "splits"


def _get_golden_dir() -> Path:
    return PROJECT_ROOT / "data" / "golden"


def _validate_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Validate that required columns exist."""
    required = ["text", "label"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {name}: {missing}")
    return df


def load_train_data() -> pd.DataFrame:
    """Load training data. Raises if not found."""
    path = _get_split_dir() / "train.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Training data not found: {path}\n"
            "Run: python scripts/create_model_splits.py"
        )
    df = pd.read_csv(path, low_memory=False)
    return _validate_columns(df, "train")


def load_dev_data() -> pd.DataFrame:
    """Load development data. Raises if not found."""
    path = _get_split_dir() / "dev.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Development data not found: {path}\n"
            "Run: python scripts/create_model_splits.py"
        )
    df = pd.read_csv(path, low_memory=False)
    return _validate_columns(df, "dev")


def load_test_data() -> pd.DataFrame:
    """Load test data. Raises if not found."""
    path = _get_split_dir() / "test.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Test data not found: {path}\n"
            "Run: python scripts/create_model_splits.py"
        )
    df = pd.read_csv(path, low_memory=False)
    return _validate_columns(df, "test")


def load_golden_data() -> pd.DataFrame:
    """Load golden evaluation data (read-only).

    Returns a DataFrame with 'text' and 'label' columns.
    Prints a warning that this is locked evaluation data.
    """
    print("WARNING: Loading golden evaluation data. This data is evaluation-only.")
    print("Do NOT use for training, tuning, or development decisions.")

    golden_path = _get_golden_dir() / "golden_set.jsonl"
    if not golden_path.exists():
        raise FileNotFoundError(
            f"Golden data not found: {golden_path}\n"
            "Run Phase 6 annotation first."
        )

    records = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        raise ValueError("Golden set is empty.")

    df = pd.DataFrame(records)
    # Standardize columns
    if "customer_message" in df.columns:
        df = df.rename(columns={"customer_message": "text"})
    if "gold_intent" in df.columns:
        df = df.rename(columns={"gold_intent": "label"})

    return _validate_columns(df, "golden")


def load_split_metadata() -> dict:
    """Load split metadata."""
    path = _get_split_dir() / "split_metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"Split metadata not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def prevent_golden_writes(split_name: str) -> None:
    """Raise an error if someone tries to use golden for training."""
    if split_name.lower() == "golden":
        raise ValueError(
            "Golden data must NOT be used for training or tuning. "
            "Use train/dev/test splits instead."
        )

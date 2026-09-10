"""Tests for Phase 3 EDA utilities and analysis."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.eda_utils import (
    calculate_brand_statistics,
    calculate_conversation_statistics,
    calculate_duplicate_statistics,
    calculate_response_time_statistics,
    calculate_text_statistics,
    detect_columns,
    detect_noise_features,
    summarize_dataframe,
    summarize_missing_values,
)


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_simple_df() -> pd.DataFrame:
    """Create a small synthetic dataframe for testing."""
    return pd.DataFrame({
        "tweet_id": [1, 2, 3, 4, 5, 6, 7, 8],
        "text": [
            "Hello, I need help with my order",
            "Sure! Can you share your order number?",
            "It's 12345",
            "Thanks, we'll look into it",
            "Hello, I need help with my order",  # exact duplicate text
            "My package is late @support #help",
            "We apologize for the delay. Visit https://example.com for updates",
            "Thank you so much!",
        ],
        "conversation_id": [1, 1, 1, 1, 2, 3, 3, 3],
        "in_reply_to_tweet_id": [np.nan, 1, 2, 3, np.nan, np.nan, 6, 7],
        "author_id": ["u1", "u2", "u1", "u2", "u1", "u3", "u4", "u3"],
        "inbound": ["true", "false", "true", "false", "true", "true", "false", "true"],
        "created_at": [
            "2024-01-01 10:00:00",
            "2024-01-01 10:05:00",
            "2024-01-01 10:10:00",
            "2024-01-01 10:15:00",
            "2024-01-02 12:00:00",
            "2024-01-03 09:00:00",
            "2024-01-03 09:30:00",
            "2024-01-03 09:35:00",
        ],
    })


# ---------------------------------------------------------------------------
# Tests: Schema detection
# ---------------------------------------------------------------------------

def test_detect_columns():
    df = make_simple_df()
    col_map = detect_columns(df)
    assert col_map["text"] == "text"
    assert col_map["tweet_id"] == "tweet_id"
    assert col_map["conversation_id"] == "conversation_id"
    assert col_map["in_reply_to_tweet_id"] == "in_reply_to_tweet_id"
    assert col_map["author_id"] == "author_id"
    assert col_map["inbound"] == "inbound"
    assert col_map["created_at"] == "created_at"


def test_detect_columns_missing():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    col_map = detect_columns(df)
    assert col_map["text"] is None
    assert col_map["conversation_id"] is None


# ---------------------------------------------------------------------------
# Tests: Dataframe summary
# ---------------------------------------------------------------------------

def test_summarize_dataframe():
    df = make_simple_df()
    summary = summarize_dataframe(df)
    assert summary["rows"] == 8
    assert summary["columns"] == 7
    assert "tweet_id" in summary["column_names"]
    assert summary["memory_mb"] >= 0


def test_summarize_missing_values():
    df = make_simple_df()
    missing = summarize_missing_values(df)
    assert "text" in missing
    assert missing["text"]["missing_count"] == 0
    # in_reply_to_tweet_id has NaN values
    assert missing["in_reply_to_tweet_id"]["missing_count"] > 0


# ---------------------------------------------------------------------------
# Tests: Text statistics
# ---------------------------------------------------------------------------

def test_calculate_text_statistics():
    texts = pd.Series(["Hello world", "Short", "This is a longer message with more words"])
    stats = calculate_text_statistics(texts, label="test")
    assert stats["count"] == 3
    assert stats["empty_count"] == 0
    assert stats["mean_char_length"] > 0
    assert stats["median_char_length"] > 0
    assert stats["max_char_length"] == max(len(t) for t in texts)


def test_calculate_text_statistics_empty():
    texts = pd.Series(["", "  ", "Hello"])
    stats = calculate_text_statistics(texts)
    assert stats["empty_count"] == 2


# ---------------------------------------------------------------------------
# Tests: Conversation statistics
# ---------------------------------------------------------------------------

def test_calculate_conversation_statistics():
    df = make_simple_df()
    stats = calculate_conversation_statistics(df, "conversation_id")
    assert stats["unique_conversations"] == 3
    assert stats["single_message_count"] == 1  # conversation 2 has 1 message
    assert stats["multi_message_count"] == 2  # conversations 1 and 3
    assert stats["max_length"] == 4  # conversation 1 has 4 messages


# ---------------------------------------------------------------------------
# Tests: Duplicate statistics
# ---------------------------------------------------------------------------

def test_calculate_duplicate_statistics():
    df = make_simple_df()
    stats = calculate_duplicate_statistics(df, text_col="text", id_col="tweet_id")
    assert stats["exact_row_duplicates"] == 0  # no exact row duplicates
    assert stats["duplicate_ids"] == 0  # all IDs unique
    # There is a duplicate text (rows 1 and 5 have same text)
    assert stats["duplicate_texts"] >= 1


# ---------------------------------------------------------------------------
# Tests: Response time statistics
# ---------------------------------------------------------------------------

def test_calculate_response_time_statistics():
    df = make_simple_df()
    stats = calculate_response_time_statistics(
        df, "conversation_id", "created_at", "inbound"
    )
    assert stats is not None
    assert stats["sample_size"] > 0
    assert stats["median_seconds"] >= 0
    assert stats["mean_seconds"] >= 0


def test_calculate_response_time_statistics_no_inbound():
    df = make_simple_df().drop(columns=["inbound"])
    stats = calculate_response_time_statistics(
        df, "conversation_id", "created_at", "inbound"
    )
    assert stats is None


# ---------------------------------------------------------------------------
# Tests: Noise detection
# ---------------------------------------------------------------------------

def test_detect_noise_features():
    texts = pd.Series([
        "Hello https://example.com",
        "@support help me",
        "This is #broken",
        "WHAT IS THIS!!!",
        "Normal message",
    ])
    noise = detect_noise_features(texts)
    assert noise["url_pct"] == 20.0  # 1 out of 5
    assert noise["mention_pct"] == 20.0
    assert noise["hashtag_pct"] == 20.0
    assert noise["repeated_punct_pct"] == 20.0


# ---------------------------------------------------------------------------
# Tests: Brand statistics
# ---------------------------------------------------------------------------

def test_calculate_brand_statistics():
    df = pd.DataFrame({
        "brand": ["A", "A", "B", "B", "B"],
        "conversation_id": [1, 1, 2, 2, 3],
    })
    stats = calculate_brand_statistics(df, "brand", "conversation_id")
    assert stats["unique_brands"] == 2
    assert "A" in stats["conversations_per_brand"]
    assert "B" in stats["conversations_per_brand"]


# ---------------------------------------------------------------------------
# Tests: Scripts exist and are valid
# ---------------------------------------------------------------------------

def test_conversation_integrity_script_exists():
    script = PROJECT_ROOT / "scripts" / "analyze_conversation_integrity.py"
    assert script.exists()

    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_eda_notebook_exists():
    notebook = PROJECT_ROOT / "notebooks" / "02_exploratory_data_analysis.ipynb"
    assert notebook.exists()

    with open(notebook, "r") as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4
    assert len(nb["cells"]) > 0


def test_eda_report_exists():
    report = PROJECT_ROOT / "reports" / "phase_3_eda.md"
    assert report.exists()
    content = report.read_text()
    assert "Phase 3" in content
    assert "Limitations" in content


def test_eda_utils_module_imports():
    """Verify that the EDA utils module can be imported."""
    result = subprocess.run(
        [sys.executable, "-c", "from src.data.eda_utils import detect_columns; print('OK')"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "OK" in result.stdout

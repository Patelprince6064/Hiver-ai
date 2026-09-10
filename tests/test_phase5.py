"""Tests for Phase 5 intent discovery and taxonomy."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.intents.message_extraction import (
    analyze_text_quality,
    create_intent_discovery_dataset,
    filter_usable_messages,
    identify_customer_messages,
    normalize_text,
)
from scripts.validate_intent_taxonomy import validate_snake_case, validate_taxonomy


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_message_df() -> pd.DataFrame:
    """Create a synthetic dataframe with customer messages."""
    return pd.DataFrame({
        "tweet_id": [1, 2, 3, 4, 5, 6],
        "text": [
            "Where is my order?",
            "I need a refund",
            "Thanks for the help!",
            "@Brand help me",
            "",
            "My package is late",
        ],
        "conversation_id": [1, 1, 2, 3, 4, 5],
        "inbound": ["true", "true", "true", "true", "true", "false"],
    })


def make_taxonomy() -> dict:
    """Create a valid synthetic taxonomy."""
    return {
        "taxonomy_version": "1.0",
        "selected_brand": "TestBrand",
        "intents": [
            {
                "intent_id": "intent_01",
                "name": "order_tracking",
                "description": "Customer asks about order status or delivery",
                "in_scope": True,
                "examples": ["Where is my order?", "When will it arrive?"],
                "confusable_with": ["delivery_delay"],
                "include": ["Order status inquiries"],
                "exclude": ["Refund requests"],
            },
            {
                "intent_id": "intent_02",
                "name": "refund_request",
                "description": "Customer explicitly requests a refund",
                "in_scope": True,
                "examples": ["I want my money back", "Can I get a refund?"],
                "confusable_with": ["cancellation"],
                "include": ["Explicit refund requests"],
                "exclude": ["Cancellation without refund request"],
            },
            {
                "intent_id": "intent_03",
                "name": "delivery_delay",
                "description": "Customer reports late delivery",
                "in_scope": True,
                "examples": ["My package is late", "Where is my delivery?"],
                "confusable_with": ["order_tracking"],
                "include": ["Late delivery reports"],
                "exclude": ["Order status inquiries"],
            },
            {
                "intent_id": "intent_04",
                "name": "account_access",
                "description": "Customer has login or account issues",
                "in_scope": True,
                "examples": ["I can't login", "My account is locked"],
                "confusable_with": ["billing_issue"],
                "include": ["Login failures", "Account lockouts"],
                "exclude": ["Billing questions"],
            },
            {
                "intent_id": "intent_05",
                "name": "technical_support",
                "description": "Customer reports a technical problem",
                "in_scope": True,
                "examples": ["The app isn't working", "I'm getting an error"],
                "confusable_with": ["account_access"],
                "include": ["Technical failures", "Error messages"],
                "exclude": ["Account access issues"],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tests: Text normalization
# ---------------------------------------------------------------------------

def test_normalize_text():
    result = normalize_text("Hello WORLD https://example.com @user")
    assert result == "hello world [URL] [MENTION]"


def test_normalize_text_empty():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""


def test_normalize_text_whitespace():
    result = normalize_text("  hello   world  ")
    assert result == "hello world"


# ---------------------------------------------------------------------------
# Tests: Customer message identification
# ---------------------------------------------------------------------------

def test_identify_customer_messages():
    df = make_message_df()
    col_map = {"inbound": "inbound"}
    mask = identify_customer_messages(df, col_map)
    assert mask.sum() == 5  # 5 inbound=true messages


def test_identify_customer_messages_no_inbound():
    df = make_message_df().drop(columns=["inbound"])
    col_map = {}
    mask = identify_customer_messages(df, col_map)
    # Fallback: no signals, returns all False
    assert mask.sum() == 0


# ---------------------------------------------------------------------------
# Tests: Message filtering
# ---------------------------------------------------------------------------

def test_filter_usable_messages():
    df = make_message_df()
    filtered = filter_usable_messages(df, "text", min_length=2)
    # Excludes empty string (row 4)
    assert len(filtered) == 5


def test_filter_usable_messages_short():
    df = make_message_df()
    filtered = filter_usable_messages(df, "text", min_length=5)
    # Excludes empty and very short messages
    assert len(filtered) < 6


# ---------------------------------------------------------------------------
# Tests: Intent discovery dataset creation
# ---------------------------------------------------------------------------

def test_create_intent_discovery_dataset():
    df = make_message_df()
    col_map = {"inbound": "inbound", "text": "text"}
    discovery = create_intent_discovery_dataset(df, col_map, "text")
    assert "normalized_text" in discovery.columns
    assert len(discovery) > 0


def test_create_intent_discovery_dataset_sample():
    df = make_message_df()
    col_map = {"inbound": "inbound", "text": "text"}
    discovery = create_intent_discovery_dataset(df, col_map, "text", sample_size=2)
    assert len(discovery) <= 2


# ---------------------------------------------------------------------------
# Tests: Text quality analysis
# ---------------------------------------------------------------------------

def test_analyze_text_quality():
    df = make_message_df()
    quality = analyze_text_quality(df, "text")
    assert quality["total_messages"] == 6
    assert quality["empty_messages"] >= 1


# ---------------------------------------------------------------------------
# Tests: Taxonomy validation
# ---------------------------------------------------------------------------

def test_validate_snake_case():
    assert validate_snake_case("order_tracking") is True
    assert validate_snake_case("refund_request") is True
    assert validate_snake_case("Order_Tracking") is False
    assert validate_snake_case("order-tracking") is False
    assert validate_snake_case("order tracking") is False


def test_validate_taxonomy_valid():
    taxonomy = make_taxonomy()
    issues = validate_taxonomy(taxonomy)
    assert len(issues) == 0


def test_validate_taxonomy_missing_intents():
    taxonomy = {"taxonomy_version": "1.0", "selected_brand": "Test"}
    issues = validate_taxonomy(taxonomy)
    assert any(i["check"] == "top_level" and "intents" in i["message"] for i in issues)


def test_validate_taxonomy_duplicate_ids():
    taxonomy = make_taxonomy()
    taxonomy["intents"][1]["intent_id"] = "intent_01"  # Duplicate
    issues = validate_taxonomy(taxonomy)
    assert any("Duplicate intent_id" in i["message"] for i in issues)


def test_validate_taxonomy_duplicate_names():
    taxonomy = make_taxonomy()
    taxonomy["intents"][1]["name"] = "order_tracking"  # Duplicate
    issues = validate_taxonomy(taxonomy)
    assert any("Duplicate name" in i["message"] for i in issues)


def test_validate_taxonomy_bad_name():
    taxonomy = make_taxonomy()
    taxonomy["intents"][0]["name"] = "Order Tracking"  # Not snake_case
    issues = validate_taxonomy(taxonomy)
    assert any("not snake_case" in i["message"] for i in issues)


def test_validate_taxonomy_no_examples():
    taxonomy = make_taxonomy()
    taxonomy["intents"][0]["examples"] = []
    issues = validate_taxonomy(taxonomy)
    assert any("No examples" in i["message"] for i in issues)


# ---------------------------------------------------------------------------
# Tests: Scripts exist
# ---------------------------------------------------------------------------

def test_prepare_intent_discovery_script():
    script = PROJECT_ROOT / "scripts" / "prepare_intent_discovery.py"
    assert script.exists()
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_validate_intent_taxonomy_script():
    script = PROJECT_ROOT / "scripts" / "validate_intent_taxonomy.py"
    assert script.exists()
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_message_extraction_module_imports():
    result = subprocess.run(
        [sys.executable, "-c", "from src.intents.message_extraction import identify_customer_messages; print('OK')"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# Tests: Reports and docs exist
# ---------------------------------------------------------------------------

def test_labeling_guide_exists():
    guide = PROJECT_ROOT / "docs" / "INTENT_LABELING_GUIDE.md"
    assert guide.exists()
    content = guide.read_text()
    assert "Primary Intent" in content
    assert "Multi-Intent" in content


def test_intent_analysis_report_exists():
    report = PROJECT_ROOT / "reports" / "phase_5_intent_analysis.md"
    assert report.exists()
    content = report.read_text()
    assert "Phase 5" in content
    assert "Taxonomy" in content


def test_intent_discovery_notebook_exists():
    notebook = PROJECT_ROOT / "notebooks" / "03_intent_discovery.ipynb"
    assert notebook.exists()
    with open(notebook, "r") as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4

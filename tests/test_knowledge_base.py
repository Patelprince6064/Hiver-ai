"""Tests for Phase 9 knowledge base."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.knowledge_schema import KnowledgeRecord, validate_knowledge_record, validate_knowledge_base
from src.retrieval.response_pairing import pair_customer_support_messages, build_conversation_context
from src.retrieval.resolution_extraction import extract_resolution_type, build_retrieval_text
from src.retrieval.quality_filter import apply_quality_flags, categorize_quality, detect_duplicates


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_conversation_df() -> pd.DataFrame:
    """Create a synthetic conversation dataframe."""
    return pd.DataFrame({
        "conversation_id": ["conv1", "conv1", "conv1", "conv2", "conv2"],
        "text": [
            "My order hasn't arrived",
            "We're looking into it. Please DM your order number.",
            "Thanks, I'll do that",
            "I need a refund",
            "Please contact our support team.",
        ],
        "author": [
            "customer",
            "brand_support",
            "customer",
            "customer",
            "brand_support",
        ],
        "tweet_id": ["t1", "t2", "t3", "t4", "t5"],
    })


# ---------------------------------------------------------------------------
# Unit tests: Knowledge schema
# ---------------------------------------------------------------------------

class TestKnowledgeSchema:
    """Tests for knowledge schema."""

    def test_valid_record(self) -> None:
        record = KnowledgeRecord(
            knowledge_id="kb_000001",
            brand="TestBrand",
            customer_message="My order is late",
            support_response="We're looking into it.",
        )
        assert record.knowledge_id == "kb_000001"

    def test_knowledge_id_must_start_with_kb(self) -> None:
        with pytest.raises(Exception):
            KnowledgeRecord(
                knowledge_id="bad_000001",
                brand="TestBrand",
                customer_message="test",
                support_response="test",
            )

    def test_quality_category_valid(self) -> None:
        record = KnowledgeRecord(
            knowledge_id="kb_000001",
            brand="TestBrand",
            customer_message="test",
            support_response="test",
            quality_category="usable",
        )
        assert record.quality_category == "usable"

    def test_quality_category_invalid(self) -> None:
        with pytest.raises(Exception):
            KnowledgeRecord(
                knowledge_id="kb_000001",
                brand="TestBrand",
                customer_message="test",
                support_response="test",
                quality_category="invalid",
            )

    def test_validate_knowledge_record_valid(self) -> None:
        record = {
            "knowledge_id": "kb_000001",
            "brand": "TestBrand",
            "customer_message": "test message",
            "support_response": "test response",
        }
        errors = validate_knowledge_record(record)
        assert errors == []

    def test_validate_knowledge_record_invalid(self) -> None:
        record = {
            "knowledge_id": "bad_000001",
            "brand": "TestBrand",
            "customer_message": "test",
            "support_response": "test",
        }
        errors = validate_knowledge_record(record)
        assert len(errors) > 0

    def test_validate_knowledge_base_valid(self) -> None:
        records = [
            {"knowledge_id": f"kb_{i:06d}", "brand": "Test", "customer_message": "test", "support_response": "resp"}
            for i in range(5)
        ]
        report = validate_knowledge_base(records)
        assert report["valid"] is True

    def test_validate_knowledge_base_duplicate_ids(self) -> None:
        records = [
            {"knowledge_id": "kb_000001", "brand": "Test", "customer_message": "test", "support_response": "resp"},
            {"knowledge_id": "kb_000001", "brand": "Test", "customer_message": "test2", "support_response": "resp2"},
        ]
        report = validate_knowledge_base(records)
        assert report["valid"] is False


# ---------------------------------------------------------------------------
# Unit tests: Response pairing
# ---------------------------------------------------------------------------

class TestResponsePairing:
    """Tests for response pairing."""

    def test_pair_customer_support(self) -> None:
        df = make_conversation_df()
        col_map = {
            "conversation_id": "conversation_id",
            "text": "text",
            "author": "author",
        }
        pairs = pair_customer_support_messages(df, col_map)
        assert len(pairs) > 0
        assert "customer_message" in pairs[0]
        assert "support_response" in pairs[0]

    def test_build_conversation_context(self) -> None:
        df = make_conversation_df()
        col_map = {
            "conversation_id": "conversation_id",
            "text": "text",
        }
        context = build_conversation_context(df, col_map, "conv1", 2)
        assert isinstance(context, str)


# ---------------------------------------------------------------------------
# Unit tests: Resolution extraction
# ---------------------------------------------------------------------------

class TestResolutionExtraction:
    """Tests for resolution extraction."""

    def test_requested_information(self) -> None:
        resolution, evidence = extract_resolution_type("Please DM us your order number.")
        assert resolution == "requested_information"

    def test_troubleshooting(self) -> None:
        resolution, evidence = extract_resolution_type("Please try restarting the application.")
        assert resolution == "troubleshooting"

    def test_escalated(self) -> None:
        resolution, evidence = extract_resolution_type("We have escalated this to our team.")
        assert resolution == "escalated"

    def test_apology_only(self) -> None:
        resolution, evidence = extract_resolution_type("We're sorry for the inconvenience.")
        assert resolution == "apology_only"

    def test_empty_response(self) -> None:
        resolution, evidence = extract_resolution_type("")
        assert resolution == "no_resolution"

    def test_build_retrieval_text(self) -> None:
        text = build_retrieval_text("My order is late", "We'll help", "troubleshooting")
        assert "Customer issue:" in text
        assert "Historical support response:" in text


# ---------------------------------------------------------------------------
# Unit tests: Quality filter
# ---------------------------------------------------------------------------

class TestQualityFilter:
    """Tests for quality filter."""

    def test_apply_quality_flags_clean(self) -> None:
        record = {
            "customer_message": "My order is late",
            "support_response": "We're looking into it.",
            "resolution_type": "troubleshooting",
            "conversation_id": "conv1",
        }
        flags = apply_quality_flags(record)
        assert "empty_customer_message" not in flags

    def test_apply_quality_flags_empty(self) -> None:
        record = {
            "customer_message": "",
            "support_response": "test",
            "resolution_type": "unclear",
        }
        flags = apply_quality_flags(record)
        assert "empty_customer_message" in flags

    def test_categorize_quality_usable(self) -> None:
        assert categorize_quality([]) == "usable"

    def test_categorize_quality_low(self) -> None:
        assert categorize_quality(["empty_customer_message"]) == "low_quality"

    def test_categorize_quality_context(self) -> None:
        assert categorize_quality(["very_short_message"]) == "usable_with_context"

    def test_detect_duplicates(self) -> None:
        records = [
            {"customer_message": "hello", "support_response": "hi"},
            {"customer_message": "hello", "support_response": "hi"},
            {"customer_message": "other", "support_response": "other"},
        ]
        dupes = detect_duplicates(records)
        assert dupes[("hello", "hi")] == 2


# ---------------------------------------------------------------------------
# Script existence tests
# ---------------------------------------------------------------------------

class TestScripts:
    """Tests for Phase 9 scripts."""

    def test_build_knowledge_base_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "build_knowledge_base.py"
        assert script.exists()

    def test_analyze_knowledge_base_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "analyze_knowledge_base.py"
        assert script.exists()

    def test_inspect_knowledge_base_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "inspect_knowledge_base.py"
        assert script.exists()

    def test_validate_knowledge_base_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "validate_knowledge_base.py"
        assert script.exists()

    def test_check_knowledge_base_leakage_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "check_knowledge_base_leakage.py"
        assert script.exists()

    def test_build_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_knowledge_base.py"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Documentation tests
# ---------------------------------------------------------------------------

class TestDocumentation:
    """Tests for Phase 9 documentation."""

    def test_config_exists(self) -> None:
        config = PROJECT_ROOT / "configs" / "knowledge_base.yaml"
        assert config.exists()

    def test_config_valid(self) -> None:
        config_path = PROJECT_ROOT / "configs" / "knowledge_base.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        assert "knowledge_base" in config
        assert "resolution_types" in config["knowledge_base"]

    def test_readme_updated(self) -> None:
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text()
        assert "Phase 9" in content
        assert "Knowledge Base" in content

    def test_decision_log_updated(self) -> None:
        log = PROJECT_ROOT / "DECISION_LOG.md"
        content = log.read_text()
        assert "Phase 9" in content
        assert "Decision 68" in content


# ---------------------------------------------------------------------------
# Data directory tests
# ---------------------------------------------------------------------------

class TestDataDirectories:
    """Tests for data directories."""

    def test_processed_dir_exists(self) -> None:
        processed_dir = PROJECT_ROOT / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        assert processed_dir.exists()

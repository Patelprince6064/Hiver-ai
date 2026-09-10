"""Tests for Phase 6 golden evaluation set."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.golden_schema import (
    GoldenExample,
    GoldenSetMetadata,
    load_golden_metadata,
    load_golden_set,
    save_golden_metadata,
    save_golden_set,
    validate_golden_example,
    validate_golden_metadata,
    validate_golden_set,
)


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_golden_example(
    golden_id: str = "gold_0001",
    gold_intent: str = "order_tracking",
    intent_confidence: str = "HIGH",
    ambiguous: bool = False,
) -> dict:
    """Create a valid synthetic golden example."""
    return {
        "golden_id": golden_id,
        "conversation_id": "conv_001",
        "message_id": "msg_001",
        "brand": "TestBrand",
        "customer_message": "Where is my order?",
        "context_messages": ["I placed an order last week"],
        "gold_intent": gold_intent,
        "intent_confidence": intent_confidence,
        "ambiguous": ambiguous,
        "label_notes": "",
        "sampling_category": ["representative"],
        "expected_escalation": None,
        "escalation_reason": None,
        "source_split": "golden",
    }


def make_golden_set(n: int = 5) -> list[dict]:
    """Create a valid synthetic golden set."""
    intents = ["order_tracking", "refund_request", "technical_support", "account_access", "general_inquiry"]
    return [
        make_golden_example(golden_id=f"gold_{i+1:04d}", gold_intent=intents[i % len(intents)])
        for i in range(n)
    ]


def make_metadata() -> dict:
    """Create valid synthetic metadata."""
    return {
        "version": "1.0",
        "size": 5,
        "selected_brand": "TestBrand",
        "sampling_seed": 42,
        "annotation_method": "human",
        "locked": False,
        "intent_taxonomy_version": "1.0",
    }


# ---------------------------------------------------------------------------
# Unit tests: Schema validation
# ---------------------------------------------------------------------------

class TestGoldenExample:
    """Tests for GoldenExample schema."""

    def test_valid_example(self) -> None:
        example = make_golden_example()
        validated = GoldenExample(**example)
        assert validated.golden_id == "gold_0001"
        assert validated.gold_intent == "order_tracking"

    def test_golden_id_must_start_with_gold(self) -> None:
        example = make_golden_example(golden_id="bad_0001")
        with pytest.raises(Exception):
            GoldenExample(**example)

    def test_intent_confidence_valid(self) -> None:
        for conf in ["HIGH", "MEDIUM", "LOW"]:
            example = make_golden_example(intent_confidence=conf)
            validated = GoldenExample(**example)
            assert validated.intent_confidence == conf

    def test_intent_confidence_invalid(self) -> None:
        example = make_golden_example(intent_confidence="VERY_HIGH")
        with pytest.raises(Exception):
            GoldenExample(**example)

    def test_customer_message_not_empty(self) -> None:
        example = make_golden_example()
        example["customer_message"] = ""
        with pytest.raises(Exception):
            GoldenExample(**example)

    def test_customer_message_whitespace_only(self) -> None:
        example = make_golden_example()
        example["customer_message"] = "   "
        with pytest.raises(Exception):
            GoldenExample(**example)

    def test_sampling_category_valid(self) -> None:
        for cat in ["representative", "rare_intent", "difficult", "confusable", "short", "multi_intent", "noisy"]:
            example = make_golden_example()
            example["sampling_category"] = [cat]
            validated = GoldenExample(**example)
            assert cat in validated.sampling_category

    def test_sampling_category_invalid(self) -> None:
        example = make_golden_example()
        example["sampling_category"] = ["invalid_category"]
        with pytest.raises(Exception):
            GoldenExample(**example)

    def test_ambiguous_flag(self) -> None:
        example = make_golden_example(ambiguous=True)
        validated = GoldenExample(**example)
        assert validated.ambiguous is True

    def test_optional_fields_default(self) -> None:
        example = make_golden_example()
        example.pop("context_messages", None)
        validated = GoldenExample(**example)
        assert validated.label_notes == ""
        assert validated.expected_escalation is None
        assert validated.escalation_reason is None
        assert validated.context_messages == []


# ---------------------------------------------------------------------------
# Unit tests: GoldenSetMetadata
# ---------------------------------------------------------------------------

class TestGoldenSetMetadata:
    """Tests for GoldenSetMetadata schema."""

    def test_valid_metadata(self) -> None:
        metadata = make_metadata()
        validated = GoldenSetMetadata(**metadata)
        assert validated.version == "1.0"
        assert validated.size == 5

    def test_metadata_defaults(self) -> None:
        metadata = {"size": 10, "selected_brand": "Brand"}
        validated = GoldenSetMetadata(**metadata)
        assert validated.version == "1.0"
        assert validated.sampling_seed == 42
        assert validated.locked is False


# ---------------------------------------------------------------------------
# Unit tests: Validation functions
# ---------------------------------------------------------------------------

class TestValidationFunctions:
    """Tests for validation functions."""

    def test_validate_golden_example_valid(self) -> None:
        example = make_golden_example()
        errors = validate_golden_example(example)
        assert errors == []

    def test_validate_golden_example_invalid(self) -> None:
        example = make_golden_example(golden_id="bad_0001")
        errors = validate_golden_example(example)
        assert len(errors) > 0

    def test_validate_golden_set_valid(self) -> None:
        examples = make_golden_set()
        report = validate_golden_set(examples)
        assert report["valid"] is True
        assert report["total_examples"] == 5

    def test_validate_golden_set_duplicate_ids(self) -> None:
        examples = make_golden_set()
        examples[1]["golden_id"] = "gold_0001"  # Duplicate
        report = validate_golden_set(examples)
        assert report["valid"] is False
        assert any("Duplicate" in e for e in report["errors"])

    def test_validate_golden_set_missing_field(self) -> None:
        examples = make_golden_set()
        del examples[0]["gold_intent"]
        report = validate_golden_set(examples)
        assert report["valid"] is False

    def test_validate_golden_set_with_valid_intents(self) -> None:
        examples = make_golden_set()
        valid_intents = {"order_tracking", "refund_request", "technical_support", "account_access", "general_inquiry"}
        report = validate_golden_set(examples, valid_intents=valid_intents)
        assert report["valid"] is True
        assert len(report["warnings"]) == 0

    def test_validate_golden_set_with_invalid_intent(self) -> None:
        examples = make_golden_set()
        valid_intents = {"order_tracking"}  # Missing other intents
        report = validate_golden_set(examples, valid_intents=valid_intents)
        assert len(report["warnings"]) > 0

    def test_validate_golden_set_high_low_confidence(self) -> None:
        examples = make_golden_set(n=10)
        for i in range(5):
            examples[i]["intent_confidence"] = "LOW"
        report = validate_golden_set(examples)
        assert any("LOW confidence" in w for w in report["warnings"])

    def test_validate_golden_set_high_ambiguous(self) -> None:
        examples = make_golden_set(n=10)
        for i in range(5):
            examples[i]["ambiguous"] = True
        report = validate_golden_set(examples)
        assert any("ambiguous" in w for w in report["warnings"])

    def test_validate_golden_metadata_valid(self) -> None:
        metadata = make_metadata()
        errors = validate_golden_metadata(metadata)
        assert errors == []

    def test_validate_golden_metadata_invalid(self) -> None:
        metadata = make_metadata()
        del metadata["size"]
        errors = validate_golden_metadata(metadata)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# Unit tests: File I/O
# ---------------------------------------------------------------------------

class TestFileIO:
    """Tests for JSONL file I/O."""

    def test_save_and_load_golden_set(self, tmp_path: Path) -> None:
        examples = make_golden_set()
        path = tmp_path / "golden_set.jsonl"
        save_golden_set(examples, path)
        loaded = load_golden_set(path)
        assert len(loaded) == 5
        assert loaded[0]["golden_id"] == "gold_0001"

    def test_save_and_load_metadata(self, tmp_path: Path) -> None:
        metadata = make_metadata()
        path = tmp_path / "metadata.json"
        save_golden_metadata(metadata, path)
        loaded = load_golden_metadata(path)
        assert loaded["version"] == "1.0"
        assert loaded["size"] == 5

    def test_load_empty_golden_set(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        loaded = load_golden_set(path)
        assert loaded == []


# ---------------------------------------------------------------------------
# Integration tests: Scripts
# ---------------------------------------------------------------------------

class TestScripts:
    """Integration tests for Phase 6 scripts."""

    def test_build_golden_candidates_script_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "build_golden_candidates.py"
        assert script.exists(), f"Script not found: {script}"

    def test_annotate_golden_script_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "annotate_golden.py"
        assert script.exists(), f"Script not found: {script}"

    def test_audit_golden_set_script_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "audit_golden_set.py"
        assert script.exists(), f"Script not found: {script}"

    def test_check_golden_leakage_script_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "check_golden_leakage.py"
        assert script.exists(), f"Script not found: {script}"

    def test_validate_golden_schema_script_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "validate_golden_schema.py"
        assert script.exists(), f"Script not found: {script}"

    def test_build_golden_candidates_help(self) -> None:
        script = PROJECT_ROOT / "scripts" / "build_golden_candidates.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "pool-size" in result.stdout.lower() or "pool" in result.stdout.lower()

    def test_audit_golden_set_missing_data(self) -> None:
        script = PROJECT_ROOT / "scripts" / "audit_golden_set.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should fail gracefully (no data)
        assert result.returncode == 1

    def test_check_golden_leakage_missing_data(self) -> None:
        script = PROJECT_ROOT / "scripts" / "check_golden_leakage.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should fail gracefully (no data)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Documentation tests
# ---------------------------------------------------------------------------

class TestDocumentation:
    """Tests for Phase 6 documentation."""

    def test_annotation_guide_exists(self) -> None:
        doc = PROJECT_ROOT / "docs" / "GOLDEN_SET_ANNOTATION_GUIDE.md"
        assert doc.exists(), f"Documentation not found: {doc}"

    def test_annotation_guide_not_empty(self) -> None:
        doc = PROJECT_ROOT / "docs" / "GOLDEN_SET_ANNOTATION_GUIDE.md"
        content = doc.read_text()
        assert len(content) > 100

    def test_sampling_methodology_exists(self) -> None:
        report = PROJECT_ROOT / "reports" / "golden_sampling_methodology.md"
        assert report.exists(), f"Report not found: {report}"

    def test_intent_coverage_exists(self) -> None:
        report = PROJECT_ROOT / "reports" / "golden_intent_coverage.md"
        assert report.exists(), f"Report not found: {report}"

    def test_readme_updated(self) -> None:
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text()
        assert "Golden" in content
        assert "golden" in content.lower()

    def test_decision_log_updated(self) -> None:
        log = PROJECT_ROOT / "DECISION_LOG.md"
        content = log.read_text()
        assert "Phase 6" in content
        assert "Decision 48" in content


# ---------------------------------------------------------------------------
# Data file tests
# ---------------------------------------------------------------------------

class TestDataFiles:
    """Tests for golden set data files."""

    def test_golden_dir_exists(self) -> None:
        golden_dir = PROJECT_ROOT / "data" / "golden"
        assert golden_dir.exists(), f"Golden directory not found: {golden_dir}"

    def test_golden_readme_exists(self) -> None:
        readme = PROJECT_ROOT / "data" / "golden" / "README.md"
        assert readme.exists(), f"Golden README not found: {readme}"

    def test_gitkeep_exists(self) -> None:
        gitkeep = PROJECT_ROOT / "data" / "golden" / ".gitkeep"
        assert gitkeep.exists(), f".gitkeep not found: {gitkeep}"

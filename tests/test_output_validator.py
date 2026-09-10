"""Tests for output validator."""

import pytest
from src.generation.output_validator import OutputValidator


class TestOutputValidator:
    def test_valid_reply(self):
        v = OutputValidator()
        result = v.validate("Please DM us your order number.")
        assert result.is_valid is True
        assert result.status == "success"

    def test_empty_reply(self):
        v = OutputValidator()
        result = v.validate("")
        assert result.is_valid is False
        assert result.status == "invalid_output"
        assert "Empty output" in result.errors

    def test_insufficient_evidence(self):
        v = OutputValidator()
        result = v.validate("INSUFFICIENT_EVIDENCE")
        assert result.is_valid is True
        assert result.status == "insufficient_evidence"

    def test_too_long(self):
        v = OutputValidator(max_reply_length=20)
        result = v.validate("This is a very long reply that exceeds the limit.")
        assert result.is_valid is False
        assert "too long" in result.errors[0].lower()

    def test_internal_terms(self):
        v = OutputValidator()
        result = v.validate("The FAISS index found the embedding.")
        assert result.is_valid is True
        assert any("faiss" in w.lower() for w in result.warnings)

    def test_valid_evidence_ids(self):
        v = OutputValidator()
        result = v.validate(
            "Hello",
            evidence_ids=["kb_001", "kb_002"],
        )
        assert result.is_valid is True

    def test_invalid_evidence_ids(self):
        v = OutputValidator()
        result = v.validate(
            "Hello",
            evidence_ids=["kb_001", "kb_999"],
        )
        assert result.is_valid is True  # Evidence IDs don't invalidate

    def test_get_params(self):
        v = OutputValidator(max_reply_length=100)
        params = v.get_params()
        assert params["max_reply_length"] == 100

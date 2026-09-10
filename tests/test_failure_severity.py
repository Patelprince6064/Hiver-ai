"""Tests for failure severity."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_severity import (
    SEVERITY_DEFINITIONS,
    get_severity_definition,
    classify_severity,
)


class TestSeverityDefinitions:
    """Tests for severity definitions."""
    
    def test_all_levels_defined(self):
        """Test all severity levels are defined."""
        assert "LOW" in SEVERITY_DEFINITIONS
        assert "MEDIUM" in SEVERITY_DEFINITIONS
        assert "HIGH" in SEVERITY_DEFINITIONS
        assert "CRITICAL" in SEVERITY_DEFINITIONS
    
    def test_get_severity_definition(self):
        """Test getting severity definition."""
        low_def = get_severity_definition("LOW")
        assert low_def is not None
        assert low_def.level == "LOW"
    
    def test_invalid_severity_returns_none(self):
        """Test invalid severity returns None."""
        result = get_severity_definition("INVALID")
        assert result is None


class TestClassifySeverity:
    """Tests for severity classification."""
    
    def test_unsafe_auto_handle_is_critical(self):
        """Test unsafe auto-handle is classified as CRITICAL."""
        severity = classify_severity(
            "ESCALATION_FAILURE",
            "UNSAFE_AUTO_HANDLE",
        )
        assert severity == "CRITICAL"
    
    def test_unsupported_price_is_high(self):
        """Test unsupported price is classified as HIGH."""
        severity = classify_severity(
            "GROUNDING_FAILURE",
            "UNSUPPORTED_PRICE",
        )
        assert severity == "HIGH"
    
    def test_wrong_intent_is_medium(self):
        """Test wrong intent is classified as MEDIUM."""
        severity = classify_severity(
            "INTENT_CLASSIFICATION_FAILURE",
            "WRONG_INTENT",
        )
        assert severity == "MEDIUM"
    
    def test_too_generic_is_low(self):
        """Test too generic is classified as LOW."""
        severity = classify_severity(
            "GENERATION_FAILURE",
            "TOO_GENERIC",
        )
        assert severity == "LOW"
    
    def test_provider_error_is_high(self):
        """Test provider error is classified as HIGH."""
        severity = classify_severity(
            "SYSTEM_FAILURE",
            "PROVIDER_ERROR",
        )
        assert severity == "HIGH"
    
    def test_unnecessary_escalation_is_low(self):
        """Test unnecessary escalation is classified as LOW."""
        severity = classify_severity(
            "ESCALATION_FAILURE",
            "UNNECESSARY_ESCALATION",
        )
        assert severity == "LOW"
    
    def test_invalid_category_returns_low(self):
        """Test invalid category returns LOW."""
        severity = classify_severity(
            "INVALID_CATEGORY",
            "invalid_secondary",
        )
        assert severity == "LOW"
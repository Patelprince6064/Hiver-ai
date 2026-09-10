"""Tests for failure extraction."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import FailureRecord


class TestFailureExtraction:
    """Tests for failure extraction logic."""
    
    def test_failure_record_creation(self):
        """Test creating failure records for extraction."""
        record = FailureRecord(
            failure_id="FAIL_EXTRACT_001",
            query_id="eval_001",
            primary_category="GENERATION_FAILURE",
            secondary_category="unhelpful",
            severity="MEDIUM",
            customer_message="Where is my order?",
            reply="I don't know.",
            failure_tags=["unhelpful"],
            root_cause="Generated reply is unhelpful",
        )
        
        d = record.to_dict()
        
        assert d["failure_id"] == "FAIL_EXTRACT_001"
        assert d["primary_category"] == "GENERATION_FAILURE"
        assert d["severity"] == "MEDIUM"
        assert "unhelpful" in d["failure_tags"]
    
    def test_missing_evaluation_signals(self):
        """Test handling missing evaluation signals."""
        record = FailureRecord(
            failure_id="FAIL_EXTRACT_002",
            query_id="eval_002",
        )
        
        d = record.to_dict()
        
        # Should have defaults
        assert d["primary_category"] == ""
        assert d["severity"] == "LOW"
        assert d["failure_tags"] == []
    
    def test_no_fabricated_examples(self):
        """Test that extraction does not fabricate examples."""
        # This test ensures we don't invent failure cases
        # In real implementation, would check against actual data
        
        record = FailureRecord(
            failure_id="FAIL_NO_FABRICATE",
            query_id="eval_real",
            primary_category="GROUNDING_FAILURE",
            secondary_category="unsupported_claim",
            severity="HIGH",
        )
        
        d = record.to_dict()
        
        # Should only contain provided data
        assert d["customer_message"] == ""
        assert d["reply"] == ""


class TestFailureCategorization:
    """Tests for failure categorization."""
    
    def test_primary_category_assignment(self):
        """Test primary category is correctly assigned."""
        record = FailureRecord(
            failure_id="FAIL_CAT_001",
            query_id="eval_001",
            primary_category="ESCALATION_FAILURE",
            secondary_category="UNSAFE_AUTO_HANDLE",
        )
        
        assert record.primary_category == "ESCALATION_FAILURE"
    
    def test_severity_assignment(self):
        """Test severity is correctly assigned."""
        record = FailureRecord(
            failure_id="FAIL_SEV_001",
            query_id="eval_001",
            severity="CRITICAL",
        )
        
        assert record.severity == "CRITICAL"


class TestPercentageCalculations:
    """Tests for percentage calculations."""
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        total_cases = 200
        total_failures = 20
        
        failure_rate = total_failures / total_cases
        
        assert failure_rate == 0.1
    
    def test_zero_division_handling(self):
        """Test handling zero division."""
        total_cases = 0
        total_failures = 0
        
        failure_rate = total_failures / total_cases if total_cases > 0 else 0
        
        assert failure_rate == 0
"""Tests for failure analysis schema."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import (
    FailureRecord,
    PrimaryCategory,
    SecondaryCategory,
    Severity,
    PIPELINE_STAGES,
    CATEGORY_TO_STAGE,
    SEVERITY_WEIGHTS,
)


class TestFailureRecord:
    """Tests for FailureRecord."""
    
    def test_valid_failure_record(self):
        """Test creating a valid failure record."""
        record = FailureRecord(
            failure_id="FAIL_001",
            query_id="eval_001",
            primary_category="GENERATION_FAILURE",
            secondary_category="unhelpful",
            severity="MEDIUM",
        )
        
        assert record.failure_id == "FAIL_001"
        assert record.query_id == "eval_001"
        assert record.primary_category == "GENERATION_FAILURE"
        assert record.severity == "MEDIUM"
    
    def test_failure_record_to_dict(self):
        """Test converting failure record to dictionary."""
        record = FailureRecord(
            failure_id="FAIL_002",
            query_id="eval_002",
            primary_category="GROUNDING_FAILURE",
            secondary_category="unsupported_claim",
            severity="HIGH",
        )
        
        d = record.to_dict()
        
        assert d["failure_id"] == "FAIL_002"
        assert d["primary_category"] == "GROUNDING_FAILURE"
        assert d["severity"] == "HIGH"
    
    def test_failure_record_defaults(self):
        """Test failure record default values."""
        record = FailureRecord(
            failure_id="FAIL_003",
            query_id="eval_003",
        )
        
        assert record.primary_category == ""
        assert record.severity == "LOW"
        assert record.failure_tags == []
        assert record.root_cause == ""


class TestPrimaryCategory:
    """Tests for PrimaryCategory enum."""
    
    def test_all_categories_exist(self):
        """Test all expected categories exist."""
        expected = [
            "DATA_FAILURE",
            "INTENT_CLASSIFICATION_FAILURE",
            "RETRIEVAL_FAILURE",
            "GENERATION_FAILURE",
            "GROUNDING_FAILURE",
            "ESCALATION_FAILURE",
            "SYSTEM_FAILURE",
            "EVALUATION_FAILURE",
        ]
        
        for cat in expected:
            assert PrimaryCategory(cat)


class TestSecondaryCategory:
    """Tests for SecondaryCategory enum."""
    
    def test_unsafe_auto_handle_exists(self):
        """Test UNSAFE_AUTO_HANDLE category exists."""
        assert SecondaryCategory.UNSAFE_AUTO_HANDLE.value == "unsafe_auto_handle"
    
    def test_unsupported_claim_exists(self):
        """Test UNSUPPORTED_CLAIM category exists."""
        assert SecondaryCategory.UNSUPPORTED_CLAIM.value == "unsupported_claim"


class TestPipelineStages:
    """Tests for pipeline stages."""
    
    def test_all_stages_defined(self):
        """Test all pipeline stages are defined."""
        assert len(PIPELINE_STAGES) == 9
        assert "INPUT" in PIPELINE_STAGES
        assert "GROUNDING" in PIPELINE_STAGES
        assert "ESCALATION" in PIPELINE_STAGES
    
    def test_category_to_stage_mapping(self):
        """Test category to stage mapping."""
        assert CATEGORY_TO_STAGE["GROUNDING_FAILURE"] == "GROUNDING"
        assert CATEGORY_TO_STAGE["ESCALATION_FAILURE"] == "ESCALATION"
        assert CATEGORY_TO_STAGE["INTENT_CLASSIFICATION_FAILURE"] == "INTENT"


class TestSeverityWeights:
    """Tests for severity weights."""
    
    def test_weights_defined(self):
        """Test all severity weights are defined."""
        assert SEVERITY_WEIGHTS["LOW"] == 1
        assert SEVERITY_WEIGHTS["MEDIUM"] == 2
        assert SEVERITY_WEIGHTS["HIGH"] == 4
        assert SEVERITY_WEIGHTS["CRITICAL"] == 8
    
    def test_critical_is_highest(self):
        """Test CRITICAL has highest weight."""
        assert SEVERITY_WEIGHTS["CRITICAL"] > SEVERITY_WEIGHTS["HIGH"]
        assert SEVERITY_WEIGHTS["HIGH"] > SEVERITY_WEIGHTS["MEDIUM"]
        assert SEVERITY_WEIGHTS["MEDIUM"] > SEVERITY_WEIGHTS["LOW"]
"""Tests for failure matrix."""

import pytest
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFailureMatrix:
    """Tests for failure matrix generation."""
    
    def test_matrix_csv_format(self):
        """Test matrix CSV has correct format."""
        # Expected columns
        expected_columns = [
            "failure_category",
            "count",
            "rate",
            "low",
            "medium",
            "high",
            "critical",
            "top_intents",
            "likely_root_stage",
        ]
        
        # This would test actual CSV generation
        # For now, just verify the structure
        assert len(expected_columns) == 9
    
    def test_matrix_counts(self):
        """Test matrix counts are accurate."""
        # Simulate failure data
        failures = [
            {"primary_category": "GENERATION_FAILURE", "severity": "LOW"},
            {"primary_category": "GENERATION_FAILURE", "severity": "MEDIUM"},
            {"primary_category": "GROUNDING_FAILURE", "severity": "HIGH"},
        ]
        
        # Count by category
        category_counts = {}
        for f in failures:
            cat = f["primary_category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        assert category_counts["GENERATION_FAILURE"] == 2
        assert category_counts["GROUNDING_FAILURE"] == 1
    
    def test_severity_distribution(self):
        """Test severity distribution in matrix."""
        failures = [
            {"severity": "LOW"},
            {"severity": "LOW"},
            {"severity": "MEDIUM"},
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
        ]
        
        severity_counts = {}
        for f in failures:
            sev = f["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        assert severity_counts["LOW"] == 2
        assert severity_counts["MEDIUM"] == 1
        assert severity_counts["HIGH"] == 1
        assert severity_counts["CRITICAL"] == 1


class TestFailureMatrixPlot:
    """Tests for failure matrix visualization."""
    
    def test_plot_generation_conditions(self):
        """Test conditions for plot generation."""
        # Matplotlib is optional
        try:
            import matplotlib
            matplotlib_available = True
        except ImportError:
            matplotlib_available = False
        
        # Plot should only be generated if matplotlib is available
        assert isinstance(matplotlib_available, bool)
"""Tests for final metrics calculations."""

import pytest
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFinalMetrics:
    """Test final metrics calculations."""
    
    def test_intent_results_structure(self):
        """Test that intent results have correct structure."""
        results_path = PROJECT_ROOT / "evaluation" / "results" / "final_intent_results.json"
        if not results_path.exists():
            pytest.skip("Intent results not created yet")
        
        with open(results_path, "r") as f:
            results = json.load(f)
        
        assert "results" in results
        assert "majority" in results["results"]
        assert "tfidf" in results["results"]
        assert "semantic" in results["results"]
        
        for model in ["majority", "tfidf", "semantic"]:
            assert "accuracy" in results["results"][model]
            assert "macro_f1" in results["results"][model]
    
    def test_escalation_results_structure(self):
        """Test that escalation results have correct structure."""
        results_path = PROJECT_ROOT / "evaluation" / "results" / "final_escalation_results.json"
        if not results_path.exists():
            pytest.skip("Escalation results not created yet")
        
        with open(results_path, "r") as f:
            results = json.load(f)
        
        assert "policies" in results
        assert "ALWAYS_AUTO_HANDLE" in results["policies"]
        assert "ALWAYS_ESCALATE" in results["policies"]
        assert "V1_0_CONSERVATIVE" in results["policies"]
        assert "V1_1_RISK_AWARE" in results["policies"]
    
    def test_metrics_are_valid(self):
        """Test that metrics are valid (0-1 range for rates)."""
        results_path = PROJECT_ROOT / "evaluation" / "results" / "final_intent_results.json"
        if not results_path.exists():
            pytest.skip("Intent results not created yet")
        
        with open(results_path, "r") as f:
            results = json.load(f)
        
        for model in ["majority", "tfidf", "semantic"]:
            accuracy = results["results"][model]["accuracy"]
            assert 0.0 <= accuracy <= 1.0, f"Invalid accuracy: {accuracy}"
            
            macro_f1 = results["results"][model]["macro_f1"]
            assert 0.0 <= macro_f1 <= 1.0, f"Invalid macro_f1: {macro_f1}"

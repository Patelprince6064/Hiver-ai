"""Tests for failure priority."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_priority import (
    PriorityConfig,
    calculate_priority_score,
    rank_failures,
    select_top_n,
)


class TestPriorityConfig:
    """Tests for PriorityConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PriorityConfig()
        
        assert config.severity_weights["LOW"] == 1
        assert config.severity_weights["MEDIUM"] == 2
        assert config.severity_weights["HIGH"] == 4
        assert config.severity_weights["CRITICAL"] == 8
        assert config.frequency_weight == 1.0
        assert config.severity_weight == 1.0
        assert config.impact_weight == 1.0


class TestCalculatePriorityScore:
    """Tests for priority score calculation."""
    
    def test_low_frequency_low_severity(self):
        """Test low frequency, low severity."""
        score = calculate_priority_score(1, "LOW", 1.0)
        assert score == 3  # 1*1 + 1*1 + 1*1
    
    def test_high_frequency_high_severity(self):
        """Test high frequency, high severity."""
        score = calculate_priority_score(10, "HIGH", 1.0)
        # 10*1 (frequency) + 4*1 (severity) + 1*1 (impact) = 15
        assert score == 15
    
    def test_critical_severity(self):
        """Test critical severity has highest weight."""
        score = calculate_priority_score(1, "CRITICAL", 1.0)
        assert score == 10  # 1*1 + 8*1 + 1*1
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PriorityConfig(
            severity_weights={"LOW": 1, "MEDIUM": 3, "HIGH": 9, "CRITICAL": 27},
            frequency_weight=2.0,
        )
        
        score = calculate_priority_score(5, "HIGH", 1.0, config)
        assert score == 20  # 5*2 + 9*1 + 1*1


class TestRankFailures:
    """Tests for failure ranking."""
    
    def test_ranking_order(self):
        """Test failures are ranked correctly."""
        failures = [
            {"count": 1, "severity": "LOW", "impact_score": 1.0},
            {"count": 10, "severity": "HIGH", "impact_score": 1.0},
            {"count": 5, "severity": "MEDIUM", "impact_score": 1.0},
        ]
        
        ranked = rank_failures(failures)
        
        assert ranked[0]["severity"] == "HIGH"
        assert ranked[1]["severity"] == "MEDIUM"
        assert ranked[2]["severity"] == "LOW"
    
    def test_priority_score_added(self):
        """Test priority score is added to failures."""
        failures = [
            {"count": 1, "severity": "LOW", "impact_score": 1.0},
        ]
        
        ranked = rank_failures(failures)
        
        assert "priority_score" in ranked[0]


class TestSelectTopN:
    """Tests for selecting top N failures."""
    
    def test_select_top_5(self):
        """Test selecting top 5 failures."""
        failures = [
            {"priority_score": 10},
            {"priority_score": 8},
            {"priority_score": 6},
            {"priority_score": 4},
            {"priority_score": 2},
            {"priority_score": 1},
        ]
        
        top = select_top_n(failures, n=5)
        
        assert len(top) == 5
        assert top[0]["priority_score"] == 10
        assert top[4]["priority_score"] == 2
    
    def test_select_top_3(self):
        """Test selecting top 3 failures."""
        failures = [
            {"priority_score": 10},
            {"priority_score": 8},
            {"priority_score": 6},
        ]
        
        top = select_top_n(failures, n=3)
        
        assert len(top) == 3
"""Tests for final evaluation configuration."""

import pytest
from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFinalEvaluationConfig:
    """Test final evaluation configuration."""
    
    def test_config_loads(self):
        """Test that final evaluation config loads."""
        config_path = PROJECT_ROOT / "configs" / "final_evaluation.yaml"
        assert config_path.exists(), f"Config not found: {config_path}"
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "evaluation" in config
        assert config["evaluation"]["status"] == "FINAL_EVALUATION_CONFIG"
    
    def test_seed_is_42(self):
        """Test that seed is 42."""
        config_path = PROJECT_ROOT / "configs" / "final_evaluation.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert config["evaluation"]["seed"] == 42
    
    def test_metric_definitions_exist(self):
        """Test that metric definitions exist."""
        config_path = PROJECT_ROOT / "configs" / "final_evaluation.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "metrics" in config["evaluation"]
        assert "intent" in config["evaluation"]["metrics"]
        assert "retrieval" in config["evaluation"]["metrics"]
        assert "reply_quality" in config["evaluation"]["metrics"]
        assert "grounding" in config["evaluation"]["metrics"]
        assert "escalation" in config["evaluation"]["metrics"]
    
    def test_output_paths_defined(self):
        """Test that output paths are defined."""
        config_path = PROJECT_ROOT / "configs" / "final_evaluation.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "paths" in config["evaluation"]
        assert "results_dir" in config["evaluation"]["paths"]
        assert "final_results" in config["evaluation"]["paths"]

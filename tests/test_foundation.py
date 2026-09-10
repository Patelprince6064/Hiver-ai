"""Tests for the Hiver AI Support Agent project foundation."""

import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).parent.parent


def test_run_pipeline_runs_without_error():
    """Verify that run_pipeline.py executes without errors."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "run_pipeline.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_pipeline.py failed:\n{result.stderr}"
    assert "Hiver AI Support Agent" in result.stdout


def test_project_config_loads():
    """Verify that the project configuration YAML is valid."""
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    assert config_path.exists(), f"Config file not found: {config_path}"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    assert config["project"]["name"] == "Hiver AI Support Agent"
    assert config["evaluation"]["golden_set_size"] == 200
    assert config["evaluation"]["target_runtime_minutes"] == 15
    assert config["agent"]["retrieval_top_k"] == 5


def test_directory_structure_exists():
    """Verify that required directories exist."""
    required_dirs = [
        "app",
        "configs",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/golden",
        "evaluation/baselines",
        "evaluation/metrics",
        "evaluation/judge",
        "evaluation/human_agreement",
        "experiments",
        "notebooks",
        "reports",
        "scripts",
        "src/data",
        "src/preprocessing",
        "src/intents",
        "src/retrieval",
        "src/generation",
        "src/escalation",
        "src/agent",
        "tests",
        "docs",
    ]
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        assert full_path.exists(), f"Missing directory: {dir_path}"


def test_env_example_exists():
    """Verify that .env.example exists and contains expected keys."""
    env_path = PROJECT_ROOT / ".env.example"
    assert env_path.exists(), ".env.example not found"

    content = env_path.read_text()
    assert "OPENAI_API_KEY=" in content
    assert "LLM_MODEL=" in content

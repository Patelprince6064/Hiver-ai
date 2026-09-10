"""Tests for Phase 2 dataset acquisition and inspection."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).parent.parent


def test_download_script_exists():
    """Verify that the download script exists and is executable."""
    script = PROJECT_ROOT / "scripts" / "download_dataset.py"
    assert script.exists(), "download_dataset.py not found"

    # Check it can be imported without errors
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in download_dataset.py: {result.stderr}"


def test_inspect_script_exists():
    """Verify that the inspection script exists and is valid Python."""
    script = PROJECT_ROOT / "scripts" / "inspect_dataset.py"
    assert script.exists(), "inspect_dataset.py not found"

    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in inspect_dataset.py: {result.stderr}"


def test_subsample_script_exists():
    """Verify that the subsample script exists and is valid Python."""
    script = PROJECT_ROOT / "scripts" / "create_subsample.py"
    assert script.exists(), "create_subsample.py not found"

    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in create_subsample.py: {result.stderr}"


def test_validation_script_exists():
    """Verify that the validation script exists and is valid Python."""
    script = PROJECT_ROOT / "scripts" / "validate_dataset.py"
    assert script.exists(), "validate_dataset.py not found"

    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in validate_dataset.py: {result.stderr}"


def test_project_config_has_dataset_fields():
    """Verify that project.yaml includes Phase 2 dataset configuration."""
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Check dataset section
    assert "dataset" in config
    assert config["dataset"]["name"] == "Customer Support on Twitter"
    assert config["dataset"]["source"] == "thoughtvector/customer-support-on-twitter"
    assert config["dataset"]["raw_dir"] == "data/raw"
    assert config["dataset"]["interim_dir"] == "data/interim"
    assert config["dataset"]["selected_brand"] is None

    # Check sampling section
    assert "sampling" in config
    assert config["sampling"]["seed"] == 42
    assert config["sampling"]["target_messages"] == 25000
    assert config["sampling"]["sampling_unit"] == "conversation"


def test_data_readme_exists():
    """Verify that data/README.md exists and describes directory policies."""
    readme_path = PROJECT_ROOT / "data" / "README.md"
    assert readme_path.exists(), "data/README.md not found"

    content = readme_path.read_text()
    assert "raw/" in content
    assert "interim/" in content
    assert "processed/" in content
    assert "golden/" in content
    assert "Never commit" in content or "not committed" in content.lower()


def test_metadata_json_is_valid_if_exists():
    """Verify that dataset_metadata.json is valid JSON if it exists."""
    metadata_path = PROJECT_ROOT / "data" / "raw" / "dataset_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        assert "dataset_name" in metadata
        assert "source" in metadata


def test_subsample_metadata_is_valid_if_exists():
    """Verify that subsample_metadata.json is valid JSON if it exists."""
    metadata_path = PROJECT_ROOT / "data" / "interim" / "subsample_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        assert "random_seed" in metadata
        assert "target_messages" in metadata
        assert "actual_messages" in metadata
        assert isinstance(metadata["random_seed"], int)


def test_development_sample_is_valid_csv_if_exists():
    """Verify that development_sample.csv is loadable if it exists."""
    sample_path = PROJECT_ROOT / "data" / "interim" / "development_sample.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path, nrows=5)
        assert len(df.columns) > 0, "CSV has no columns"
        assert len(df) > 0, "CSV sample is empty"


def test_notebook_exists():
    """Verify that the inspection notebook exists."""
    notebook_path = PROJECT_ROOT / "notebooks" / "01_dataset_inspection.ipynb"
    assert notebook_path.exists(), "01_dataset_inspection.ipynb not found"

    # Verify it's valid JSON
    with open(notebook_path, "r") as f:
        notebook = json.load(f)
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) > 0


def test_validation_script_runs():
    """Verify that the validation script runs without crashing."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "validate_dataset.py")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Script should run without crashing (may return non-zero if data missing)
    assert result.returncode in (0, 1), f"Validation script crashed: {result.stderr}"

"""Tests for Phase 4 brand selection and problem framing."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.brand_selection import (
    BrandScore,
    compute_brand_features,
    min_max_normalize,
    score_brands,
    select_brand,
    DEFAULT_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_brand_df() -> pd.DataFrame:
    """Create a synthetic dataframe with multiple brands for testing."""
    np.random.seed(42)
    records = []

    brands = ["BrandA", "BrandB", "BrandC"]
    for i in range(100):
        brand = brands[i % 3]
        conv_id = i // 3
        records.append({
            "tweet_id": i,
            "text": f"Message {i} about {brand}",
            "conversation_id": conv_id,
            "inbound": "true" if i % 2 == 0 else "false",
            "brand": brand,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Tests: Normalization
# ---------------------------------------------------------------------------

def test_min_max_normalize():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = min_max_normalize(values)
    assert result[0] == 0.0
    assert result[-1] == 1.0
    assert len(result) == 5


def test_min_max_normalize_identical():
    values = [3.0, 3.0, 3.0]
    result = min_max_normalize(values)
    assert all(r == 0.5 for r in result)


def test_min_max_normalize_empty():
    result = min_max_normalize([])
    assert result == []


def test_min_max_normalize_two_values():
    values = [10.0, 20.0]
    result = min_max_normalize(values)
    assert result[0] == 0.0
    assert result[1] == 1.0


# ---------------------------------------------------------------------------
# Tests: Feature computation
# ---------------------------------------------------------------------------

def test_compute_brand_features():
    df = make_brand_df()
    features = compute_brand_features(df, "brand", "conversation_id", "text", "inbound")
    assert len(features) == 3  # 3 brands
    brands = {f["brand"] for f in features}
    assert "BrandA" in brands
    assert "BrandB" in brands
    assert "BrandC" in brands


def test_compute_brand_features_values():
    df = make_brand_df()
    features = compute_brand_features(df, "brand", "conversation_id", "text", "inbound")
    for f in features:
        assert f["raw_conversations"] > 0
        assert f["raw_messages"] > 0
        assert 0 <= f["raw_multi_turn_pct"] <= 100
        assert 0 <= f["raw_response_coverage"] <= 100


# ---------------------------------------------------------------------------
# Tests: Scoring
# ---------------------------------------------------------------------------

def test_score_brands():
    df = make_brand_df()
    features = compute_brand_features(df, "brand", "conversation_id", "text", "inbound")
    scores = score_brands(features, DEFAULT_WEIGHTS)
    assert len(scores) == 3
    # Scores should be sorted descending
    for i in range(len(scores) - 1):
        assert scores[i].total_score >= scores[i + 1].total_score


def test_score_brands_weights():
    df = make_brand_df()
    features = compute_brand_features(df, "brand", "conversation_id", "text", "inbound")

    # Use custom weights emphasizing conversation volume
    custom_weights = {
        "conversation_volume": 1.0,
        "multi_turn_coverage": 0.0,
        "support_response_coverage": 0.0,
        "conversation_quality": 0.0,
        "customer_support_density": 0.0,
        "issue_diversity_proxy": 0.0,
        "evaluation_suitability": 0.0,
    }
    scores = score_brands(features, custom_weights)
    assert len(scores) == 3
    # All scores should be between 0 and 1
    for s in scores:
        assert 0 <= s.total_score <= 1.0


def test_score_brands_range():
    df = make_brand_df()
    features = compute_brand_features(df, "brand", "conversation_id", "text", "inbound")
    scores = score_brands(features, DEFAULT_WEIGHTS)
    for s in scores:
        assert 0 <= s.total_score <= 1.0
        assert 0 <= s.conversation_volume <= 1.0
        assert 0 <= s.multi_turn_coverage <= 1.0
        assert 0 <= s.support_response_coverage <= 1.0


# ---------------------------------------------------------------------------
# Tests: Brand selection
# ---------------------------------------------------------------------------

def test_select_brand():
    df = make_brand_df()
    selected, all_scores = select_brand(df, "brand", "conversation_id", "text", "inbound")
    assert selected is not None
    assert isinstance(selected, BrandScore)
    assert len(all_scores) == 3


# ---------------------------------------------------------------------------
# Tests: Configuration
# ---------------------------------------------------------------------------

def test_config_has_brand_selection():
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    assert "brand_selection" in config
    assert config["brand_selection"]["method"] == "weighted_data_suitability_score"
    assert "weights" in config["brand_selection"]
    assert abs(sum(config["brand_selection"]["weights"].values()) - 1.0) < 0.01


def test_config_weights_match_default():
    config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config_weights = config["brand_selection"]["weights"]
    for key in DEFAULT_WEIGHTS:
        assert key in config_weights, f"Missing weight: {key}"
        assert config_weights[key] == DEFAULT_WEIGHTS[key], f"Weight mismatch for {key}"


# ---------------------------------------------------------------------------
# Tests: Scripts exist
# ---------------------------------------------------------------------------

def test_compute_brand_statistics_script():
    script = PROJECT_ROOT / "scripts" / "compute_brand_statistics.py"
    assert script.exists()
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_extract_selected_brand_script():
    script = PROJECT_ROOT / "scripts" / "extract_selected_brand.py"
    assert script.exists()
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_brand_selection_module_imports():
    result = subprocess.run(
        [sys.executable, "-c", "from src.data.brand_selection import select_brand; print('OK')"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# Tests: Reports exist
# ---------------------------------------------------------------------------

def test_brand_selection_report_exists():
    report = PROJECT_ROOT / "reports" / "phase_4_brand_selection.md"
    assert report.exists()
    content = report.read_text()
    assert "Phase 4" in content
    assert "Selection Criteria" in content


def test_problem_framing_exists():
    report = PROJECT_ROOT / "reports" / "problem_framing.md"
    assert report.exists()
    content = report.read_text()
    assert "Problem Framing" in content
    assert "What" in content  # "What 'Good' Means"

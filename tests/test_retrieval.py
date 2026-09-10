"""Tests for Phase 10 semantic retrieval."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.retrieval_schema import RetrievalResult, RetrievalResponse, build_retrieval_response
from src.evaluation.retrieval_metrics import recall_at_k, precision_at_k, mean_reciprocal_rank


# ---------------------------------------------------------------------------
# Unit tests: Retrieval schema
# ---------------------------------------------------------------------------

class TestRetrievalSchema:
    """Tests for retrieval schema."""

    def test_valid_result(self) -> None:
        result = RetrievalResult(
            rank=1,
            knowledge_id="kb_000001",
            customer_message="test",
            support_response="response",
            similarity_score=0.9,
        )
        assert result.rank == 1
        assert result.knowledge_id == "kb_000001"

    def test_build_retrieval_response(self) -> None:
        results = [
            {"knowledge_id": "kb_000001", "similarity_score": 0.9, "customer_message": "test", "support_response": "resp"},
        ]
        response = build_retrieval_response("query", results)
        assert response.retrieval_status == "success"
        assert len(response.results) == 1

    def test_empty_results(self) -> None:
        response = build_retrieval_response("query", [])
        assert response.retrieval_status == "insufficient_evidence"


# ---------------------------------------------------------------------------
# Unit tests: Retrieval metrics
# ---------------------------------------------------------------------------

class TestRetrievalMetrics:
    """Tests for retrieval metrics."""

    def test_recall_at_k(self) -> None:
        relevant = ["kb_001", "kb_002"]
        retrieved = ["kb_001", "kb_003", "kb_002"]
        assert recall_at_k(relevant, retrieved, 3) == 1.0

    def test_recall_at_k_partial(self) -> None:
        relevant = ["kb_001", "kb_002"]
        retrieved = ["kb_001", "kb_003"]
        assert recall_at_k(relevant, retrieved, 3) == 0.5

    def test_recall_at_k_none(self) -> None:
        relevant = ["kb_001"]
        retrieved = ["kb_002"]
        assert recall_at_k(relevant, retrieved, 3) == 0.0

    def test_precision_at_k(self) -> None:
        relevant = ["kb_001"]
        retrieved = ["kb_001", "kb_002", "kb_003"]
        assert precision_at_k(relevant, retrieved, 3) == 1 / 3

    def test_mrr(self) -> None:
        relevant = ["kb_002"]
        retrieved = ["kb_001", "kb_002"]
        assert mean_reciprocal_rank(relevant, retrieved) == 0.5

    def test_mrr_first(self) -> None:
        relevant = ["kb_001"]
        retrieved = ["kb_001"]
        assert mean_reciprocal_rank(relevant, retrieved) == 1.0

    def test_mrr_none(self) -> None:
        relevant = ["kb_001"]
        retrieved = ["kb_002"]
        assert mean_reciprocal_rank(relevant, retrieved) == 0.0


# ---------------------------------------------------------------------------
# Script existence tests
# ---------------------------------------------------------------------------

class TestScripts:
    """Tests for Phase 10 scripts."""

    def test_build_retrieval_index_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "build_retrieval_index.py"
        assert script.exists()

    def test_test_retrieval_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "test_retrieval.py"
        assert script.exists()

    def test_validate_retrieval_index_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "validate_retrieval_index.py"
        assert script.exists()

    def test_check_retrieval_index_leakage_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "check_retrieval_index_leakage.py"
        assert script.exists()

    def test_build_retrieval_index_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_retrieval_index.py"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0

    def test_test_retrieval_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "test_retrieval.py"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Documentation tests
# ---------------------------------------------------------------------------

class TestDocumentation:
    """Tests for Phase 10 documentation."""

    def test_config_exists(self) -> None:
        config = PROJECT_ROOT / "configs" / "retrieval.yaml"
        assert config.exists()

    def test_config_valid(self) -> None:
        config_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        assert "retrieval" in config
        assert "embedding_model" in config["retrieval"]

    def test_readme_updated(self) -> None:
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text()
        assert "Phase 10" in content
        assert "Retrieval" in content

    def test_decision_log_updated(self) -> None:
        log = PROJECT_ROOT / "DECISION_LOG.md"
        content = log.read_text()
        assert "Phase 10" in content
        assert "Decision 78" in content


# ---------------------------------------------------------------------------
# Data directory tests
# ---------------------------------------------------------------------------

class TestDataDirectories:
    """Tests for data directories."""

    def test_retrieval_index_dir_exists(self) -> None:
        index_dir = PROJECT_ROOT / "data" / "processed" / "retrieval_index"
        index_dir.mkdir(parents=True, exist_ok=True)
        assert index_dir.exists()

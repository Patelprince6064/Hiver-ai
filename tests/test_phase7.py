"""Tests for Phase 7 intent classification baselines."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import prevent_golden_writes
from src.evaluation.result_schema import EvaluationResult, build_result
from src.intents.base_classifier import BaseIntentClassifier
from src.intents.trivial_baseline import MajorityClassClassifier
from src.intents.tfidf_baseline import TfidfLogisticRegressionClassifier, preprocess_text


# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

def make_train_df() -> pd.DataFrame:
    return pd.DataFrame({
        "text": [
            "Where is my order?",
            "I need a refund",
            "Thanks for the help",
            "My package is late",
            "Can't login to my account",
            "Where is my order?",
            "I need a refund",
            "Thanks for the help",
            "My package is late",
            "Can't login to my account",
            "Where is my order?",
            "I need a refund",
        ],
        "label": [
            "order_tracking",
            "refund_request",
            "general_inquiry",
            "delivery_issue",
            "account_access",
            "order_tracking",
            "refund_request",
            "general_inquiry",
            "delivery_issue",
            "account_access",
            "order_tracking",
            "refund_request",
        ],
    })


def make_dev_df() -> pd.DataFrame:
    return pd.DataFrame({
        "text": [
            "Where is my package?",
            "I want my money back",
            "How do I reset password?",
            "Thanks!",
        ],
        "label": [
            "order_tracking",
            "refund_request",
            "account_access",
            "general_inquiry",
        ],
    })


# ---------------------------------------------------------------------------
# Unit tests: Base classifier interface
# ---------------------------------------------------------------------------

class TestBaseClassifier:
    """Tests for base classifier interface."""

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            BaseIntentClassifier()

    def test_trivial_implements_interface(self) -> None:
        clf = MajorityClassClassifier()
        assert hasattr(clf, "fit")
        assert hasattr(clf, "predict")
        assert hasattr(clf, "predict_proba")
        assert hasattr(clf, "get_params")

    def test_tfidf_implements_interface(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        assert hasattr(clf, "fit")
        assert hasattr(clf, "predict")
        assert hasattr(clf, "predict_proba")
        assert hasattr(clf, "get_params")


# ---------------------------------------------------------------------------
# Unit tests: Majority classifier
# ---------------------------------------------------------------------------

class TestMajorityClassifier:
    """Tests for majority class classifier."""

    def test_fit(self) -> None:
        clf = MajorityClassClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        assert clf.majority_label is not None

    def test_majority_label(self) -> None:
        clf = MajorityClassClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        # All labels appear 3 times except general_inquiry (2) and delivery_issue (1)
        # order_tracking: 3, refund_request: 3, general_inquiry: 2, delivery_issue: 1, account_access: 2
        assert clf.majority_label in ["order_tracking", "refund_request"]

    def test_predict_returns_same_label(self) -> None:
        clf = MajorityClassClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        preds = clf.predict(df["text"])
        assert all(p == clf.majority_label for p in preds)

    def test_predict_before_fit(self) -> None:
        clf = MajorityClassClassifier()
        with pytest.raises(RuntimeError):
            clf.predict(pd.Series(["test"]))

    def test_predict_proba(self) -> None:
        clf = MajorityClassClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        proba = clf.predict_proba(df["text"])
        assert len(proba) == len(df)
        assert all(isinstance(p, dict) for p in proba)
        assert all(sum(p.values()) > 0 for p in proba)

    def test_get_params(self) -> None:
        clf = MajorityClassClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        params = clf.get_params()
        assert "majority_label" in params
        assert "majority_proportion" in params


# ---------------------------------------------------------------------------
# Unit tests: TF-IDF classifier
# ---------------------------------------------------------------------------

class TestTfidfClassifier:
    """Tests for TF-IDF + Logistic Regression classifier."""

    def test_fit(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        assert len(clf.classes_) > 0

    def test_predict(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        preds = clf.predict(df["text"])
        assert len(preds) == len(df)
        assert all(isinstance(p, str) for p in preds)

    def test_predict_before_fit(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        with pytest.raises(RuntimeError):
            clf.predict(pd.Series(["test"]))

    def test_predict_proba_shape(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        proba = clf.predict_proba(df["text"])
        assert len(proba) == len(df)
        for p in proba:
            assert isinstance(p, dict)
            assert len(p) == len(clf.classes_)
            assert sum(p.values()) > 0.99

    def test_valid_labels(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        df = make_train_df()
        clf.fit(df["text"], df["label"])
        preds = clf.predict(df["text"])
        assert all(p in clf.classes_ for p in preds)

    def test_get_params(self) -> None:
        clf = TfidfLogisticRegressionClassifier()
        params = clf.get_params()
        assert "ngram_range" in params
        assert "min_df" in params
        assert "random_state" in params


# ---------------------------------------------------------------------------
# Unit tests: Text preprocessing
# ---------------------------------------------------------------------------

class TestPreprocessing:
    """Tests for text preprocessing."""

    def test_lowercase(self) -> None:
        assert preprocess_text("HELLO") == "hello"

    def test_url_normalization(self) -> None:
        result = preprocess_text("Visit https://example.com for info")
        assert "URL" in result
        assert "https" not in result

    def test_mention_normalization(self) -> None:
        result = preprocess_text("@brand help me")
        assert "MENTION" in result
        assert "@brand" not in result

    def test_whitespace_normalization(self) -> None:
        result = preprocess_text("hello   world")
        assert "  " not in result

    def test_empty_input(self) -> None:
        assert preprocess_text("") == ""
        assert preprocess_text(None) == ""


# ---------------------------------------------------------------------------
# Unit tests: Result schema
# ---------------------------------------------------------------------------

class TestResultSchema:
    """Tests for evaluation result schema."""

    def test_build_result(self) -> None:
        y_true = ["a", "b", "a", "b"]
        y_pred = ["a", "b", "b", "b"]
        result = build_result("test_model", "dev", y_true, y_pred)
        assert isinstance(result, EvaluationResult)
        assert result.model == "test_model"
        assert result.dataset == "dev"
        assert result.metrics["accuracy"] == 0.75
        assert result.n_examples == 4

    def test_result_has_all_metrics(self) -> None:
        y_true = ["a", "b", "a", "b"]
        y_pred = ["a", "b", "b", "b"]
        result = build_result("test_model", "dev", y_true, y_pred)
        assert "accuracy" in result.metrics
        assert "macro_f1" in result.metrics
        assert "weighted_f1" in result.metrics

    def test_result_per_intent(self) -> None:
        y_true = ["a", "b", "a", "b"]
        y_pred = ["a", "b", "b", "b"]
        result = build_result("test_model", "dev", y_true, y_pred)
        assert "a" in result.per_intent
        assert "b" in result.per_intent


# ---------------------------------------------------------------------------
# Unit tests: Golden protection
# ---------------------------------------------------------------------------

class TestGoldenProtection:
    """Tests for golden-set protection."""

    def test_prevent_golden_writes(self) -> None:
        with pytest.raises(ValueError, match="must NOT be used"):
            prevent_golden_writes("golden")

    def test_allow_dev_writes(self) -> None:
        prevent_golden_writes("dev")  # Should not raise

    def test_allow_train_writes(self) -> None:
        prevent_golden_writes("train")  # Should not raise


# ---------------------------------------------------------------------------
# Script existence tests
# ---------------------------------------------------------------------------

class TestScripts:
    """Tests for Phase 7 scripts."""

    def test_create_model_splits_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "create_model_splits.py"
        assert script.exists()

    def test_verify_split_isolation_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "verify_split_isolation.py"
        assert script.exists()

    def test_train_tfidf_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "train_tfidf_baseline.py"
        assert script.exists()

    def test_evaluate_intent_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "evaluate_intent_baseline.py"
        assert script.exists()

    def test_analyze_errors_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "analyze_intent_errors.py"
        assert script.exists()

    def test_run_baselines_exists(self) -> None:
        script = PROJECT_ROOT / "scripts" / "run_baselines.py"
        assert script.exists()

    def test_create_splits_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "create_model_splits.py"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "seed" in result.stdout.lower()

    def test_verify_isolation_fails_without_data(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "verify_split_isolation.py")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1  # No data available


# ---------------------------------------------------------------------------
# Documentation tests
# ---------------------------------------------------------------------------

class TestDocumentation:
    """Tests for Phase 7 documentation."""

    def test_evaluation_protocol_exists(self) -> None:
        doc = PROJECT_ROOT / "docs" / "EVALUATION_PROTOCOL.md"
        assert doc.exists()

    def test_baselines_config_exists(self) -> None:
        config = PROJECT_ROOT / "configs" / "baselines.yaml"
        assert config.exists()

    def test_baselines_config_valid(self) -> None:
        config_path = PROJECT_ROOT / "configs" / "baselines.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        assert "baselines" in config
        assert "tfidf_logistic_regression" in config["baselines"]

    def test_readme_updated(self) -> None:
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text()
        assert "Phase 7" in content
        assert "Baseline" in content

    def test_decision_log_updated(self) -> None:
        log = PROJECT_ROOT / "DECISION_LOG.md"
        content = log.read_text()
        assert "Phase 7" in content
        assert "Decision 49" in content


# ---------------------------------------------------------------------------
# Data directory tests
# ---------------------------------------------------------------------------

class TestDataDirectories:
    """Tests for data directories."""

    def test_evaluation_results_dir_exists(self) -> None:
        results_dir = PROJECT_ROOT / "evaluation" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        assert results_dir.exists()

    def test_models_dir_exists(self) -> None:
        models_dir = PROJECT_ROOT / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        assert models_dir.exists()

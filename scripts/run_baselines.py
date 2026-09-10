#!/usr/bin/env python3
"""Run all baselines: train, evaluate on DEV, evaluate on GOLDEN.

Usage:
    python scripts/run_baselines.py
"""

import json
import pickle
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import (
    load_dev_data,
    load_golden_data,
    load_train_data,
    prevent_golden_writes,
)
from src.evaluation.result_schema import build_result
from src.intents.trivial_baseline import MajorityClassClassifier
from src.intents.tfidf_baseline import TfidfLogisticRegressionClassifier


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "baselines.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    project_root = find_project_root()
    config = load_config()
    tfidf_config = config.get("baselines", {}).get("tfidf_logistic_regression", {})

    # Load data
    print("Loading data...")
    train_df = load_train_data()
    dev_df = load_dev_data()

    print(f"Train: {len(train_df):,}")
    print(f"Dev: {len(dev_df):,}")

    # Check golden availability
    golden_available = False
    try:
        golden_df = load_golden_data()
        golden_available = True
        print(f"Golden: {len(golden_df):,}")
    except FileNotFoundError:
        print("Golden set not found. Skipping golden evaluation.")

    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # --- Majority Baseline ---
    print("\n" + "=" * 60)
    print("MAJORITY CLASS BASELINE")
    print("=" * 60)

    clf_majority = MajorityClassClassifier()
    clf_majority.fit(train_df["text"], train_df["label"])
    print(f"Majority class: {clf_majority.majority_label} ({clf_majority.majority_proportion:.2%})")

    # DEV evaluation
    y_pred_dev = clf_majority.predict(dev_df["text"])
    result_dev = build_result(
        model="majority",
        dataset="dev",
        y_true=dev_df["label"].tolist(),
        y_pred=y_pred_dev,
        config=clf_majority.get_params(),
    )

    with open(results_dir / "trivial_baseline_dev.json", "w") as f:
        json.dump(result_dev.model_dump(), f, indent=2)

    print(f"\nDEV Results:")
    print(f"  Accuracy: {result_dev.metrics['accuracy']:.4f}")
    print(f"  Macro F1: {result_dev.metrics['macro_f1']:.4f}")
    print(f"  Weighted F1: {result_dev.metrics['weighted_f1']:.4f}")

    # GOLDEN evaluation
    if golden_available:
        prevent_golden_writes("golden")
        y_pred_golden = clf_majority.predict(golden_df["text"])
        result_golden = build_result(
            model="majority",
            dataset="golden",
            y_true=golden_df["label"].tolist(),
            y_pred=y_pred_golden,
            config=clf_majority.get_params(),
        )

        with open(results_dir / "trivial_baseline_golden.json", "w") as f:
            json.dump(result_golden.model_dump(), f, indent=2)

        print(f"\nGOLDEN Results:")
        print(f"  Accuracy: {result_golden.metrics['accuracy']:.4f}")
        print(f"  Macro F1: {result_golden.metrics['macro_f1']:.4f}")
        print(f"  Weighted F1: {result_golden.metrics['weighted_f1']:.4f}")

    # --- TF-IDF Baseline ---
    print("\n" + "=" * 60)
    print("TF-IDF + LOGISTIC REGRESSION BASELINE")
    print("=" * 60)

    clf_tfidf = TfidfLogisticRegressionClassifier(
        ngram_range=tuple(tfidf_config.get("ngram_range", [1, 2])),
        min_df=tfidf_config.get("min_df", 2),
        max_df=tfidf_config.get("max_df", 0.95),
        sublinear_tf=tfidf_config.get("sublinear_tf", True),
        max_iter=tfidf_config.get("max_iter", 1000),
        class_weight=tfidf_config.get("class_weight", "balanced"),
        random_state=tfidf_config.get("random_state", 42),
    )

    print("Training TF-IDF + LR...")
    clf_tfidf.fit(train_df["text"], train_df["label"])
    print("Training complete.")

    # Save model
    model_dir = project_root / "models" / "tfidf_baseline"
    model_dir.mkdir(parents=True, exist_ok=True)
    with open(model_dir / "model.pkl", "wb") as f:
        pickle.dump(clf_tfidf, f)

    # DEV evaluation
    y_pred_dev = clf_tfidf.predict(dev_df["text"])
    result_dev = build_result(
        model="tfidf_logistic_regression",
        dataset="dev",
        y_true=dev_df["label"].tolist(),
        y_pred=y_pred_dev,
        config=clf_tfidf.get_params(),
    )

    with open(results_dir / "tfidf_baseline_dev.json", "w") as f:
        json.dump(result_dev.model_dump(), f, indent=2)

    print(f"\nDEV Results:")
    print(f"  Accuracy: {result_dev.metrics['accuracy']:.4f}")
    print(f"  Macro F1: {result_dev.metrics['macro_f1']:.4f}")
    print(f"  Weighted F1: {result_dev.metrics['weighted_f1']:.4f}")

    # GOLDEN evaluation
    if golden_available:
        prevent_golden_writes("golden")
        y_pred_golden = clf_tfidf.predict(golden_df["text"])
        result_golden = build_result(
            model="tfidf_logistic_regression",
            dataset="golden",
            y_true=golden_df["label"].tolist(),
            y_pred=y_pred_golden,
            config=clf_tfidf.get_params(),
        )

        with open(results_dir / "tfidf_baseline_golden.json", "w") as f:
            json.dump(result_golden.model_dump(), f, indent=2)

        print(f"\nGOLDEN Results:")
        print(f"  Accuracy: {result_golden.metrics['accuracy']:.4f}")
        print(f"  Macro F1: {result_golden.metrics['macro_f1']:.4f}")
        print(f"  Weighted F1: {result_golden.metrics['weighted_f1']:.4f}")

    # Summary
    print("\n" + "=" * 60)
    print("BASELINE RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n{'Model':<30} {'Accuracy':>10} {'Macro F1':>10} {'Weighted F1':>12}")
    print("-" * 65)
    print(f"{'Majority Class':<30} {result_dev.metrics['accuracy']:>10.4f} {result_dev.metrics['macro_f1']:>10.4f} {result_dev.metrics['weighted_f1']:>12.4f}")

    # Load TF-IDF dev result
    with open(results_dir / "tfidf_baseline_dev.json", "r") as f:
        tfidf_dev = json.load(f)
    print(f"{'TF-IDF + LogReg':<30} {tfidf_dev['metrics']['accuracy']:>10.4f} {tfidf_dev['metrics']['macro_f1']:>10.4f} {tfidf_dev['metrics']['weighted_f1']:>12.4f}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

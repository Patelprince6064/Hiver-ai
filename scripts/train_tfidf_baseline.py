#!/usr/bin/env python3
"""Train TF-IDF + Logistic Regression baseline.

Usage:
    python scripts/train_tfidf_baseline.py
"""

import json
import pickle
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import load_dev_data, load_train_data
from src.evaluation.result_schema import build_result
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

    # Load config
    config = load_config()
    tfidf_config = config.get("baselines", {}).get("tfidf_logistic_regression", {})

    # Load data
    print("Loading training data...")
    train_df = load_train_data()
    print(f"Train: {len(train_df):,} examples")

    print("\nLoading development data...")
    dev_df = load_dev_data()
    print(f"Dev: {len(dev_df):,} examples")

    # Check for rare classes
    label_counts = train_df["label"].value_counts()
    rare_classes = label_counts[label_counts < 2]
    if len(rare_classes) > 0:
        print(f"\nWarning: {len(rare_classes)} intents have fewer than 2 training examples:")
        for label, count in rare_classes.items():
            print(f"  {label}: {count}")
        print("These intents may not be learnable by the classifier.")

    # Train
    print("\nTraining TF-IDF + Logistic Regression...")
    clf = TfidfLogisticRegressionClassifier(
        ngram_range=tuple(tfidf_config.get("ngram_range", [1, 2])),
        min_df=tfidf_config.get("min_df", 2),
        max_df=tfidf_config.get("max_df", 0.95),
        sublinear_tf=tfidf_config.get("sublinear_tf", True),
        max_iter=tfidf_config.get("max_iter", 1000),
        class_weight=tfidf_config.get("class_weight", "balanced"),
        random_state=tfidf_config.get("random_state", 42),
    )

    clf.fit(train_df["text"], train_df["label"])
    print("Training complete.")

    # Evaluate on dev
    print("\nEvaluating on DEV...")
    y_pred = clf.predict(dev_df["text"])
    proba = clf.predict_proba(dev_df["text"])

    result = build_result(
        model="tfidf_logistic_regression",
        dataset="dev",
        y_true=dev_df["label"].tolist(),
        y_pred=y_pred,
        proba=proba,
        config=clf.get_params(),
    )

    # Save model
    model_dir = project_root / "models" / "tfidf_baseline"
    model_dir.mkdir(parents=True, exist_ok=True)

    with open(model_dir / "model.pkl", "wb") as f:
        pickle.dump(clf, f)
    print(f"\nModel saved to: {model_dir}")

    # Save results
    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(results_dir / "tfidf_baseline_dev.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"Dev results saved to: {results_dir / 'tfidf_baseline_dev.json'}")

    # Print summary
    print(f"\n--- TF-IDF Baseline Results (DEV) ---")
    print(f"Accuracy: {result.metrics['accuracy']:.4f}")
    print(f"Macro F1: {result.metrics['macro_f1']:.4f}")
    print(f"Weighted F1: {result.metrics['weighted_f1']:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

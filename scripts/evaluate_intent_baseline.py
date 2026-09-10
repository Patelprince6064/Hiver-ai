#!/usr/bin/env python3
"""Evaluate intent classifiers on DEV and GOLDEN splits.

Usage:
    python scripts/evaluate_intent_baseline.py --model majority --dataset dev
    python scripts/evaluate_intent_baseline.py --model tfidf --dataset golden
"""

import argparse
import json
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import (
    load_dev_data,
    load_golden_data,
    prevent_golden_writes,
    load_test_data,
    load_train_data,
)
from src.evaluation.result_schema import build_result
from src.intents.trivial_baseline import MajorityClassClassifier


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "baselines.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def plot_confusion_matrix(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
    output_path: Path,
    title: str = "Confusion Matrix",
) -> None:
    """Plot and save confusion matrix."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(10, 10))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(ax=ax, cmap="Blues", xticks_rotation=45, values_format="d")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def analyze_confidence(
    proba: list[dict[str, float]],
    y_true: list[str],
    y_pred: list[str],
) -> dict:
    """Analyze prediction confidence."""
    max_probs = [max(p.values()) for p in proba]
    correct = [t == p for t, p in zip(y_true, y_pred)]

    return {
        "mean_confidence": float(np.mean(max_probs)),
        "median_confidence": float(np.median(max_probs)),
        "std_confidence": float(np.std(max_probs)),
        "mean_confidence_correct": float(np.mean([m for m, c in zip(max_probs, correct) if c])),
        "mean_confidence_incorrect": float(np.mean([m for m, c in zip(max_probs, correct) if not c])),
        "low_confidence_count": sum(1 for m in max_probs if m < 0.5),
        "low_confidence_correct": sum(1 for m, c in zip(max_probs, correct) if m < 0.5 and c),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate intent classifier.")
    parser.add_argument("--model", choices=["majority", "tfidf"], required=True)
    parser.add_argument("--dataset", choices=["dev", "golden"], required=True)
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Load data
    if args.dataset == "dev":
        df = load_dev_data()
    else:
        prevent_golden_writes("golden")
        df = load_golden_data()

    print(f"Dataset: {args.dataset} ({len(df):,} examples)")

    # Get labels
    label_counts = df["label"].value_counts()
    labels = sorted(label_counts.index.tolist())

    # Train/load model
    if args.model == "majority":
        # Train majority classifier on train data
        train_df = load_train_data()
        clf = MajorityClassClassifier()
        clf.fit(train_df["text"], train_df["label"])
        print(f"Majority class: {clf.majority_label} ({clf.majority_proportion:.2%})")
    else:
        # Load TF-IDF model
        model_path = project_root / "models" / "tfidf_baseline" / "model.pkl"
        if not model_path.exists():
            print(f"Error: Model not found at {model_path}")
            print("Run: python scripts/train_tfidf_baseline.py")
            return 1
        with open(model_path, "rb") as f:
            clf = pickle.load(f)

    # Predict
    y_pred = clf.predict(df["text"])
    proba = clf.predict_proba(df["text"])

    # Build result
    result = build_result(
        model=args.model,
        dataset=args.dataset,
        y_true=df["label"].tolist(),
        y_pred=y_pred,
        proba=proba,
        config=clf.get_params(),
    )

    # Save result
    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / f"{args.model}_baseline_{args.dataset}.json"
    with open(output_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Confusion matrix
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    cm_path = plots_dir / f"{args.model}_confusion_matrix_{args.dataset}.png"
    plot_confusion_matrix(
        df["label"].tolist(),
        y_pred,
        labels,
        cm_path,
        title=f"{args.model} Confusion Matrix ({args.dataset})",
    )
    print(f"Confusion matrix saved to: {cm_path}")

    # Confidence analysis
    if proba and any(any(v > 0 for v in p.values()) for p in proba):
        confidence = analyze_confidence(proba, df["label"].tolist(), y_pred)
        conf_path = results_dir / f"{args.model}_confidence_{args.dataset}.json"
        with open(conf_path, "w") as f:
            json.dump(confidence, f, indent=2)
        print(f"Confidence analysis saved to: {conf_path}")

    # Print summary
    print(f"\n--- {args.model} Results ({args.dataset}) ---")
    print(f"Accuracy: {result.metrics['accuracy']:.4f}")
    print(f"Macro F1: {result.metrics['macro_f1']:.4f}")
    print(f"Weighted F1: {result.metrics['weighted_f1']:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

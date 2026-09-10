#!/usr/bin/env python3
"""Evaluate the semantic intent classifier.

Usage:
    python scripts/evaluate_semantic_classifier.py --dataset dev
    python scripts/evaluate_semantic_classifier.py --dataset test
    python scripts/evaluate_semantic_classifier.py --dataset golden
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import (
    load_dev_data,
    load_golden_data,
    load_test_data,
    load_train_data,
    prevent_golden_writes,
)
from src.evaluation.result_schema import build_result
from src.intents.semantic_classifier import SemanticIntentClassifier


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "semantic_classifier.yaml"
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

    buckets = {
        "0.0-0.2": {"total": 0, "correct": 0},
        "0.2-0.4": {"total": 0, "correct": 0},
        "0.4-0.6": {"total": 0, "correct": 0},
        "0.6-0.8": {"total": 0, "correct": 0},
        "0.8-1.0": {"total": 0, "correct": 0},
    }

    for prob, is_correct in zip(max_probs, correct):
        if prob < 0.2:
            bucket = "0.0-0.2"
        elif prob < 0.4:
            bucket = "0.2-0.4"
        elif prob < 0.6:
            bucket = "0.4-0.6"
        elif prob < 0.8:
            bucket = "0.6-0.8"
        else:
            bucket = "0.8-1.0"
        buckets[bucket]["total"] += 1
        if is_correct:
            buckets[bucket]["correct"] += 1

    for bucket in buckets:
        total = buckets[bucket]["total"]
        if total > 0:
            buckets[bucket]["accuracy"] = round(buckets[bucket]["correct"] / total, 4)
        else:
            buckets[bucket]["accuracy"] = 0.0

    return {
        "mean_confidence": float(np.mean(max_probs)),
        "median_confidence": float(np.median(max_probs)),
        "std_confidence": float(np.std(max_probs)),
        "mean_confidence_correct": float(np.mean([m for m, c in zip(max_probs, correct) if c])),
        "mean_confidence_incorrect": float(np.mean([m for m, c in zip(max_probs, correct) if not c])) if any(not c for c in correct) else 0.0,
        "low_confidence_count": sum(1 for m in max_probs if m < 0.5),
        "high_confidence_incorrect": sum(1 for m, c in zip(max_probs, correct) if m > 0.8 and not c),
        "buckets": buckets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate semantic classifier.")
    parser.add_argument("--dataset", choices=["dev", "test", "golden"], required=True)
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()
    sc_config = config.get("semantic_classifier", {})

    # Load data
    if args.dataset == "dev":
        df = load_dev_data()
    elif args.dataset == "test":
        df = load_test_data()
    else:
        prevent_golden_writes("golden")
        df = load_golden_data()

    print(f"Dataset: {args.dataset} ({len(df):,} examples)")

    # Load model
    save_dir = project_root / sc_config.get("save_dir", "models/semantic_classifier")
    clf = SemanticIntentClassifier.load(save_dir)
    print(f"Embedding model: {clf.embedding_model_name}")

    # Predict
    y_pred = clf.predict(df["text"])
    proba = clf.predict_proba(df["text"])

    # Build result
    result = build_result(
        model="semantic_embedding_logistic_regression",
        dataset=args.dataset,
        y_true=df["label"].tolist(),
        y_pred=y_pred,
        proba=proba,
        config=clf.get_params(),
    )

    # Save result
    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / f"semantic_{args.dataset}_results.json"
    with open(output_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Save predictions
    predictions = []
    for i, (idx, row) in enumerate(df.iterrows()):
        predictions.append({
            "message_id": row.get("message_id", None),
            "conversation_id": row.get("conversation_id", None),
            "customer_message": row.get("text", ""),
            "gold_intent": row.get("label", ""),
            "predicted_intent": y_pred[i],
            "confidence": max(proba[i].values()),
            "correct": row.get("label", "") == y_pred[i],
        })

    predictions_path = results_dir / f"semantic_{args.dataset}_predictions.jsonl"
    with open(predictions_path, "w") as f:
        for pred in predictions:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    print(f"Predictions saved to: {predictions_path}")

    # Confusion matrix
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    labels = sorted(df["label"].unique().tolist())
    cm_path = plots_dir / f"semantic_{args.dataset}_confusion_matrix.png"
    plot_confusion_matrix(
        df["label"].tolist(),
        y_pred,
        labels,
        cm_path,
        title=f"Semantic Classifier Confusion Matrix ({args.dataset})",
    )
    print(f"Confusion matrix saved to: {cm_path}")

    # Confidence analysis
    confidence = analyze_confidence(proba, df["label"].tolist(), y_pred)
    conf_path = results_dir / f"semantic_{args.dataset}_confidence_analysis.json"
    with open(conf_path, "w") as f:
        json.dump(confidence, f, indent=2)
    print(f"Confidence analysis saved to: {conf_path}")

    # Print summary
    print(f"\n--- Semantic Classifier Results ({args.dataset}) ---")
    print(f"Accuracy: {result.metrics['accuracy']:.4f}")
    print(f"Macro F1: {result.metrics['macro_f1']:.4f}")
    print(f"Weighted F1: {result.metrics['weighted_f1']:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Analyze intent classification errors.

For the TF-IDF baseline, identifies false predictions,
most confused pairs, and confidence patterns.

Usage:
    python scripts/analyze_intent_errors.py
"""

import json
import pickle
import sys
from pathlib import Path
from collections import Counter

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import load_dev_data, load_train_data


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    project_root = find_project_root()

    # Load data
    print("Loading data...")
    train_df = load_train_data()
    dev_df = load_dev_data()

    # Load model
    model_path = project_root / "models" / "tfidf_baseline" / "model.pkl"
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print("Run: python scripts/train_tfidf_baseline.py first.")
        return 1

    with open(model_path, "rb") as f:
        clf = pickle.load(f)

    # Predict
    y_pred = clf.predict(dev_df["text"])
    proba = clf.predict_proba(dev_df["text"])

    # Get max probabilities
    max_probs = [max(p.values()) for p in proba]

    # Build error records
    records = []
    for i, (idx, row) in enumerate(dev_df.iterrows()):
        records.append({
            "message_id": row.get("message_id", None),
            "conversation_id": row.get("conversation_id", None),
            "customer_message": row.get("text", ""),
            "gold_intent": row.get("label", ""),
            "predicted_intent": y_pred[i],
            "confidence": max_probs[i],
            "correct": row.get("label", "") == y_pred[i],
        })

    errors = [r for r in records if not r["correct"]]
    correct = [r for r in records if r["correct"]]

    # Confused pairs
    confusion_pairs = Counter()
    for e in errors:
        pair = (e["gold_intent"], e["predicted_intent"])
        confusion_pairs[pair] += 1

    # High-confidence errors
    high_conf_errors = [e for e in errors if e["confidence"] > 0.8]

    # Low-confidence correct
    low_conf_correct = [e for e in correct if e["confidence"] < 0.5]

    # Save errors
    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    errors_df = pd.DataFrame(errors)
    errors_df.to_csv(results_dir / "tfidf_error_analysis.csv", index=False)
    print(f"Error analysis saved to: {results_dir / 'tfidf_error_analysis.csv'}")

    # Save confusion pairs
    confusion_data = {
        "top_confused_pairs": [
            {"gold": pair[0], "predicted": pair[1], "count": count}
            for pair, count in confusion_pairs.most_common(10)
        ],
        "high_confidence_errors": len(high_conf_errors),
        "low_confidence_correct": len(low_conf_correct),
    }

    with open(results_dir / "tfidf_confusion_pairs.json", "w") as f:
        json.dump(confusion_data, f, indent=2)

    # Print summary
    print(f"\n--- Error Analysis (DEV) ---")
    print(f"Total: {len(dev_df)}")
    print(f"Correct: {len(correct)}")
    print(f"Errors: {len(errors)}")

    print(f"\nTop confused pairs:")
    for pair, count in confusion_pairs.most_common(5):
        print(f"  {pair[0]} -> {pair[1]}: {count}")

    print(f"\nHigh-confidence errors (>0.8): {len(high_conf_errors)}")
    print(f"Low-confidence correct (<0.5): {len(low_conf_correct)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

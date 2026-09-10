#!/usr/bin/env python3
"""Analyze semantic classifier errors.

Identifies top confusion pairs and shows real examples.

Usage:
    python scripts/analyze_semantic_errors.py
    python scripts/analyze_semantic_errors.py --dataset dev
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.data_loader import load_dev_data, load_test_data
from src.intents.semantic_classifier import SemanticIntentClassifier


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze semantic classifier errors.")
    parser.add_argument("--dataset", choices=["dev", "test"], default="dev")
    args = parser.parse_args()

    project_root = find_project_root()

    # Load data
    if args.dataset == "dev":
        df = load_dev_data()
    else:
        df = load_test_data()

    print(f"Dataset: {args.dataset} ({len(df):,} examples)")

    # Load model
    save_dir = project_root / "models" / "semantic_classifier"
    clf = SemanticIntentClassifier.load(save_dir)

    # Predict
    y_pred = clf.predict(df["text"])
    proba = clf.predict_proba(df["text"])

    # Build records
    records = []
    for i, (idx, row) in enumerate(df.iterrows()):
        records.append({
            "message_id": row.get("message_id", None),
            "conversation_id": row.get("conversation_id", None),
            "customer_message": row.get("text", ""),
            "gold_intent": row.get("label", ""),
            "predicted_intent": y_pred[i],
            "confidence": max(proba[i].values()),
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

    # Error categories
    error_categories = {
        "very_short": [],
        "similar_intents": [],
        "noisy_social_media": [],
        "missing_context": [],
    }

    for e in errors:
        msg = e["customer_message"]
        if len(msg.split()) <= 3:
            error_categories["very_short"].append(e)
        if any(c in msg.lower() for c in ["@", "#", "http"]):
            error_categories["noisy_social_media"].append(e)

    # Save errors
    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    errors_df = pd.DataFrame(errors)
    errors_df.to_csv(results_dir / f"semantic_error_analysis_{args.dataset}.csv", index=False)

    # Save confusion pairs
    confusion_data = {
        "top_confused_pairs": [
            {"gold": pair[0], "predicted": pair[1], "count": count}
            for pair, count in confusion_pairs.most_common(10)
        ],
        "high_confidence_errors": len(high_conf_errors),
        "low_confidence_correct": len(low_conf_correct),
        "error_categories": {k: len(v) for k, v in error_categories.items()},
    }

    with open(results_dir / f"semantic_confusion_pairs_{args.dataset}.json", "w") as f:
        json.dump(confusion_data, f, indent=2)

    # Print summary
    print(f"\n--- Error Analysis ({args.dataset}) ---")
    print(f"Total: {len(df)}")
    print(f"Correct: {len(correct)}")
    print(f"Errors: {len(errors)}")
    print(f"Accuracy: {len(correct)/len(df):.4f}")

    print(f"\nTop confused pairs:")
    for pair, count in confusion_pairs.most_common(5):
        print(f"  {pair[0]} -> {pair[1]}: {count}")

    print(f"\nHigh-confidence errors (>0.8): {len(high_conf_errors)}")
    print(f"Low-confidence correct (<0.5): {len(low_conf_correct)}")

    print(f"\nError categories:")
    for cat, items in error_categories.items():
        print(f"  {cat}: {len(items)}")

    # Show top confusion examples
    print(f"\nTop confusion examples:")
    for pair, count in confusion_pairs.most_common(3):
        gold, pred = pair
        examples = [e for e in errors if e["gold_intent"] == gold and e["predicted_intent"] == pred]
        for e in examples[:2]:
            msg = e["customer_message"][:80]
            print(f"  [{gold} -> {pred}] conf={e['confidence']:.2f}: {msg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Evaluate reply baselines on DEV split.

Usage:
    python scripts/evaluate_reply_baselines.py [--output evaluation/results]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config() -> dict:
    with open(PROJECT_ROOT / "configs" / "generation.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate reply baselines")
    parser.add_argument("--output", default="evaluation/results", help="Output directory")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config()

    print("=" * 60)
    print("PHASE 11 — REPLY BASELINE EVALUATION")
    print("=" * 60)

    # Check prerequisites
    kb_path = PROJECT_ROOT / "data" / "processed" / "knowledge_base.jsonl"
    index_dir = PROJECT_ROOT / "data" / "processed" / "retrieval_index"
    dev_path = PROJECT_ROOT / "data" / "processed" / "splits" / "dev.csv"

    missing = []
    if not kb_path.exists():
        missing.append("knowledge_base.jsonl (run: python scripts/build_knowledge_base.py)")
    if not (index_dir / "index.faiss").exists():
        missing.append("retrieval index (run: python scripts/build_retrieval_index.py)")
    if not dev_path.exists():
        missing.append("dev.csv (run: python scripts/create_model_splits.py)")

    if missing:
        print("\nMissing prerequisites:")
        for m in missing:
            print(f"  - {m}")
        print("\nRun the above scripts first.")
        return 1

    import pandas as pd
    from src.generation.generic_baseline import GenericReplyGenerator
    from src.generation.historical_baseline import HistoricalReplyGenerator
    from src.generation.reply_schema import ReplyOutput
    from src.retrieval.retriever import HistoricalSupportRetriever
    from src.evaluation.reply_metrics import evaluate_reply_baselines

    # Load data
    dev_df = pd.read_csv(dev_path)
    print(f"\nDEV split: {len(dev_df)} examples")

    if "text" not in dev_df.columns or "label" not in dev_df.columns:
        print("ERROR: dev.csv must have 'text' and 'label' columns")
        return 1

    # Initialize retriever
    print("Loading retrieval index...")
    retriever = HistoricalSupportRetriever()
    retriever.load(index_dir)

    # Initialize generators
    generic_gen = GenericReplyGenerator(
        fallback_reply=config["generation"]["generic_baseline"]["fallback_reply"],
    )
    historical_gen = HistoricalReplyGenerator(
        retriever=retriever,
        top_k=config["generation"]["historical_baseline"]["top_k"],
        require_evidence=config["generation"]["historical_baseline"]["require_evidence"],
    )

    # Run evaluation
    generic_preds = []
    historical_preds = []
    n_with_intent = 0

    print(f"Running evaluation on {len(dev_df)} queries...")
    for _, row in dev_df.iterrows():
        message = row["text"]
        intent = row["label"]

        if pd.notna(intent):
            n_with_intent += 1

        generic_result = generic_gen.generate(
            customer_message=message,
            intent=intent if pd.notna(intent) else None,
        )
        generic_preds.append(generic_result.model_dump())

        hist_result = historical_gen.generate(
            customer_message=message,
            intent=intent if pd.notna(intent) else None,
        )
        historical_preds.append(hist_result.model_dump())

    # Compute metrics
    metrics = evaluate_reply_baselines(generic_preds, historical_preds)

    # Save predictions
    generic_out = output_dir / "generic_reply_predictions.jsonl"
    with open(generic_out, "w", encoding="utf-8") as f:
        for pred in generic_preds:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    print(f"\nGeneric predictions: {generic_out}")

    hist_out = output_dir / "historical_reply_predictions.jsonl"
    with open(hist_out, "w", encoding="utf-8") as f:
        for pred in historical_preds:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    print(f"Historical predictions: {hist_out}")

    # Save comparison
    comparison_out = output_dir / "reply_baseline_comparison.json"
    comparison = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_queries": len(dev_df),
        "n_with_intent": n_with_intent,
        "metrics": metrics,
    }
    with open(comparison_out, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"Comparison: {comparison_out}")

    # Print results
    gm = metrics["generic_baseline"]
    hm = metrics["historical_baseline"]

    print(f"\n{'Metric':<30} {'Generic':>12} {'Historical':>12}")
    print("-" * 56)
    print(f"{'Response Coverage':<30} {gm['response_coverage']:>12.1%} {hm['response_coverage']:>12.1%}")
    print(f"{'Evidence Availability':<30} {gm['evidence_availability']:>12.1%} {hm['evidence_availability']:>12.1%}")
    print(f"{'Intent Consistency':<30} {gm['intent_consistency']:>12.1%} {hm['intent_consistency']:>12.1%}")
    print(f"{'Safety Risk Rate':<30} {gm['safety_risk_rate']:>12.1%} {hm['safety_risk_rate']:>12.1%}")

    if hm.get("similarity_distribution"):
        sd = hm["similarity_distribution"]
        print(f"\nHistorical Similarity Distribution:")
        print(f"  Mean: {sd['mean']:.4f}  Median: {sd['median']:.4f}")
        print(f"  Min:  {sd['min']:.4f}  Max: {sd['max']:.4f}")

    if hm.get("reply_length"):
        rl = hm["reply_length"]
        print(f"\nHistorical Reply Length (words):")
        print(f"  Mean: {rl['mean']:.1f}  Median: {rl['median']:.1f}")
        print(f"  Min:  {rl['min']:.0f}  Max: {rl['max']:.0f}")

    print(f"\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

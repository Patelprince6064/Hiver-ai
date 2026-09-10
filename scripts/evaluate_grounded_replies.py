#!/usr/bin/env python3
"""Evaluate grounded replies against baselines.

Usage:
    python scripts/evaluate_grounded_replies.py [--mock] [--output evaluation/results]
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config() -> dict:
    with open(PROJECT_ROOT / "configs" / "generation.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate grounded replies")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM provider")
    parser.add_argument("--output", default="evaluation/results", help="Output directory")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config()
    llm_config = config["generation"].get("grounded_llm", {})

    print("=" * 60)
    print("PHASE 12 — GROUNDED REPLY EVALUATION")
    print("=" * 60)

    # Check prerequisites
    dev_path = PROJECT_ROOT / "data" / "processed" / "splits" / "dev.csv"
    index_dir = PROJECT_ROOT / "data" / "processed" / "retrieval_index"

    missing = []
    if not dev_path.exists():
        missing.append("dev.csv (run: python scripts/create_model_splits.py)")
    if not (index_dir / "index.faiss").exists():
        missing.append("retrieval index (run: python scripts/build_retrieval_index.py)")

    if missing:
        print("\nMissing prerequisites:")
        for m in missing:
            print(f"  - {m}")
        return 1

    import pandas as pd
    from src.retrieval.retriever import HistoricalSupportRetriever
    from src.generation.grounded_reply_generator import GroundedReplyGenerator
    from src.generation.evidence_selector import EvidenceSelector
    from src.generation.context_budget import ContextBudget
    from src.evaluation.grounding_checks import run_grounding_checks

    # Load data
    dev_df = pd.read_csv(dev_path)
    print(f"\nDEV split: {len(dev_df)} examples")

    # Initialize retriever
    print("Loading retrieval index...")
    retriever = HistoricalSupportRetriever()
    retriever.load(index_dir)

    # Initialize LLM provider
    if args.mock:
        from src.generation.llm.mock_provider import MockLLMProvider
        llm_provider = MockLLMProvider(
            response="Sorry about the delay. Please DM us your order number so we can check the status."
        )
    else:
        from src.generation.llm.openai_provider import OpenAIProvider
        try:
            llm_provider = OpenAIProvider(
                model=llm_config.get("model", "gpt-4o-mini"),
                timeout=llm_config.get("timeout", 30),
                max_retries=llm_config.get("max_retries", 1),
            )
        except Exception as e:
            print(f"Error initializing OpenAI provider: {e}")
            print("Use --mock for testing without API credentials.")
            return 1

    # Initialize generator
    generator = GroundedReplyGenerator(
        retriever=retriever,
        llm_provider=llm_provider,
        evidence_selector=EvidenceSelector(
            max_evidence=llm_config.get("evidence_top_k", 3),
            min_similarity=llm_config.get("min_similarity"),
            deduplicate=llm_config.get("deduplicate_evidence", True),
        ),
        context_budget=ContextBudget(),
        temperature=llm_config.get("temperature", 0.0),
        max_tokens=llm_config.get("max_tokens", 300),
        prompt_version=llm_config.get("prompt_version", "v1"),
    )

    # Run evaluation
    predictions = []
    grounding_results = []
    n_success = 0
    n_insufficient = 0
    n_error = 0
    total_latency = 0.0

    print(f"Running evaluation on {len(dev_df)} queries...")
    for _, row in dev_df.iterrows():
        message = row["text"]
        intent = row["label"] if pd.notna(row["label"]) else None

        start = time.time()
        result = generator.generate(
            customer_message=message,
            predicted_intent=intent,
        )
        elapsed = (time.time() - start) * 1000
        total_latency += elapsed

        pred_dict = {
            "customer_message": message,
            "predicted_intent": intent,
            "intent_confidence": result.intent_confidence,
            "reply": result.reply,
            "generation_method": "grounded_llm",
            "status": result.status,
            "evidence": [
                {
                    "knowledge_id": e.knowledge_id,
                    "similarity_score": e.similarity_score,
                    "support_response": e.support_response,
                    "intent": e.intent,
                    "resolution_type": e.resolution_type,
                }
                for e in result.evidence
            ],
            "risk_flags": result.risk_flags,
            "prompt_version": result.metadata.get("prompt_version", "v1"),
            "model": result.metadata.get("model", "unknown"),
            "usage": result.metadata.get("usage", {}),
            "latency_ms": elapsed,
        }
        predictions.append(pred_dict)

        if result.status == "success":
            n_success += 1
            gc = run_grounding_checks(
                reply=result.reply or "",
                evidence=[
                    {
                        "knowledge_id": e.knowledge_id,
                        "support_response": e.support_response,
                    }
                    for e in result.evidence
                ],
                customer_message=message,
            )
            grounding_results.append({
                "customer_message": message[:100],
                "reply": (result.reply or "")[:100],
                "checks": gc.checks,
                "issues": gc.issues,
                "passed": gc.passed,
            })
        elif result.status == "insufficient_evidence":
            n_insufficient += 1
        else:
            n_error += 1

    # Save predictions
    pred_path = output_dir / "grounded_reply_predictions.jsonl"
    with open(pred_path, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    print(f"\nPredictions: {pred_path}")

    # Save grounding checks
    gc_path = output_dir / "grounding_checks.json"
    with open(gc_path, "w", encoding="utf-8") as f:
        json.dump(grounding_results, f, indent=2, ensure_ascii=False)
    print(f"Grounding checks: {gc_path}")

    # Compute metrics
    n_total = len(predictions)
    avg_latency = total_latency / n_total if n_total else 0
    grounding_pass_rate = (
        sum(1 for g in grounding_results if g["passed"]) / len(grounding_results)
        if grounding_results else 0
    )

    # Save summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_queries": n_total,
        "n_success": n_success,
        "n_insufficient": n_insufficient,
        "n_error": n_error,
        "success_rate": n_success / n_total if n_total else 0,
        "insufficient_evidence_rate": n_insufficient / n_total if n_total else 0,
        "error_rate": n_error / n_total if n_total else 0,
        "grounding_pass_rate": grounding_pass_rate,
        "avg_latency_ms": avg_latency,
        "model": llm_config.get("model", "mock"),
        "prompt_version": llm_config.get("prompt_version", "v1"),
    }
    summary_path = output_dir / "grounded_reply_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")

    # Print results
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Total queries:       {n_total}")
    print(f"Success:             {n_success} ({n_success/n_total:.1%})")
    print(f"Insufficient evidence: {n_insufficient} ({n_insufficient/n_total:.1%})")
    print(f"Errors:              {n_error} ({n_error/n_total:.1%})")
    print(f"Grounding pass rate: {grounding_pass_rate:.1%}")
    print(f"Avg latency:         {avg_latency:.0f}ms")
    print(f"Model:               {llm_config.get('model', 'mock')}")
    print(f"Prompt version:      {llm_config.get('prompt_version', 'v1')}")

    print(f"\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

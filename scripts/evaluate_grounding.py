#!/usr/bin/env python3
"""Evaluate grounding verification pipeline.

Usage:
    python scripts/evaluate_grounding.py [--mock] [--output evaluation/results]
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
    with open(PROJECT_ROOT / "configs" / "grounding.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate grounding verification")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM provider")
    parser.add_argument("--output", default="evaluation/results", help="Output directory")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config()

    print("=" * 60)
    print("PHASE 13 — GROUNDING VERIFICATION EVALUATION")
    print("=" * 60)

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
    from src.evaluation.claim_extractor import extract_claims
    from src.evaluation.evidence_support import check_claim_support
    from src.evaluation.numeric_claim_checker import check_numeric_claims
    from src.evaluation.url_checker import check_urls
    from src.evaluation.semantic_grounding import check_semantic_grounding
    from src.evaluation.grounding_score import compute_grounding_verdict
    from src.evaluation.grounding_metrics import compute_grounding_metrics
    from src.generation.reply_repair import ReplyRepairer
    from src.generation.llm.mock_provider import MockLLMProvider

    dev_df = pd.read_csv(dev_path)
    print(f"\nDEV split: {len(dev_df)} examples")

    print("Loading retrieval index...")
    retriever = HistoricalSupportRetriever()
    retriever.load(index_dir)

    if args.mock:
        llm_provider = MockLLMProvider(
            response="Sorry about the delay. Please DM us your order number so we can check the status."
        )
    else:
        from src.generation.llm.openai_provider import OpenAIProvider
        try:
            llm_provider = OpenAIProvider(
                model=config["generation"].get("grounded_llm", {}).get("model", "gpt-4o-mini"),
                timeout=30,
                max_retries=1,
            )
        except Exception as e:
            print(f"Error initializing OpenAI provider: {e}")
            print("Use --mock for testing without API credentials.")
            return 1

    generator = GroundedReplyGenerator(
        retriever=retriever,
        llm_provider=llm_provider,
        evidence_selector=EvidenceSelector(max_evidence=3),
        context_budget=ContextBudget(),
        temperature=0.0,
        max_tokens=300,
    )

    repairer = ReplyRepairer(llm_provider=llm_provider)

    verifications = []
    n_pass = 0
    n_fail = 0
    n_review = 0
    n_insufficient = 0
    n_repaired = 0
    n_repair_success = 0
    total_latency = 0.0

    print(f"Running grounding evaluation on {len(dev_df)} queries...")
    for _, row in dev_df.iterrows():
        message = row["text"]
        intent = row["label"] if pd.notna(row["label"]) else None

        start = time.time()
        result = generator.generate(
            customer_message=message,
            predicted_intent=intent,
        )
        latency_ms = (time.time() - start) * 1000
        total_latency += latency_ms

        evidence_dicts = [
            {
                "knowledge_id": e.knowledge_id,
                "support_response": e.support_response,
                "customer_message": getattr(e, "customer_message", ""),
                "similarity_score": e.similarity_score,
            }
            for e in result.evidence
        ]

        claims = extract_claims(result.reply or "")
        support_results = [
            check_claim_support(c, evidence_dicts, message) for c in claims
        ]
        numeric = check_numeric_claims(result.reply or "", evidence_dicts)
        url_check = check_urls(result.reply or "", evidence_dicts, message)
        semantic = check_semantic_grounding(result.reply or "", evidence_dicts)

        verdict = compute_grounding_verdict(
            reply_text=result.reply or "",
            claims=claims,
            support_results=support_results,
            numeric_result=numeric,
            url_result=url_check,
            semantic_result=semantic,
            evidence=evidence_dicts,
        )

        repair_attempted = False
        repair_succeeded = False
        final_status = verdict.status

        if verdict.status in ("fail", "review") and result.reply:
            repair_attempted = True
            repair_output = repairer.repair(
                customer_message=message,
                original_reply=result.reply,
                evidence=evidence_dicts,
                unsupported_claims=verdict.unsupported_claims,
            )
            if repair_output.status == "success" and repair_output.reply:
                n_repair_success += 1
                final_status = "repaired"
            else:
                final_status = "insufficient_evidence"

        if final_status == "pass" or final_status == "repaired":
            n_pass += 1
        elif final_status == "fail":
            n_fail += 1
        elif final_status == "review":
            n_review += 1
        else:
            n_insufficient += 1

        if repair_attempted:
            n_repaired += 1

        verification = {
            "customer_message": message[:200],
            "reply": (result.reply or "")[:200],
            "status": verdict.status,
            "final_status": final_status,
            "grounding_score": verdict.grounding_score,
            "claims": verdict.claims,
            "risk_flags": verdict.risk_flags,
            "unsupported_claims": verdict.unsupported_claims,
            "evidence_used": verdict.evidence_used,
            "reason": verdict.reason,
            "repair_attempted": repair_attempted,
            "repair_succeeded": repair_succeeded,
            "latency_ms": latency_ms,
        }
        verifications.append(verification)

    metrics = compute_grounding_metrics(verifications)

    ver_path = output_dir / "grounding_verifications.jsonl"
    with open(ver_path, "w", encoding="utf-8") as f:
        for v in verifications:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    print(f"\nVerifications: {ver_path}")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_queries": metrics.n_replies,
        "grounding_pass_rate": metrics.grounding_pass_rate,
        "unsupported_claim_rate": metrics.unsupported_claim_rate,
        "high_risk_unsupported_rate": metrics.high_risk_unsupported_rate,
        "repair_rate": metrics.repair_rate,
        "repair_success_rate": metrics.repair_success_rate,
        "final_rejection_rate": metrics.final_rejection_rate,
        "insufficient_evidence_rate": metrics.insufficient_evidence_rate,
        "avg_grounding_score": metrics.avg_grounding_score,
        "avg_latency_ms": total_latency / len(verifications) if verifications else 0,
        "details": metrics.details,
    }
    summary_path = output_dir / "grounding_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Total queries:             {metrics.n_replies}")
    print(f"Grounding pass rate:       {metrics.grounding_pass_rate:.1%}")
    print(f"Unsupported claim rate:    {metrics.unsupported_claim_rate:.1%}")
    print(f"High-risk unsupported:     {metrics.high_risk_unsupported_rate:.1%}")
    print(f"Repair rate:               {metrics.repair_rate:.1%}")
    print(f"Repair success rate:       {metrics.repair_success_rate:.1%}")
    print(f"Final rejection rate:      {metrics.final_rejection_rate:.1%}")
    print(f"Insufficient evidence:     {metrics.insufficient_evidence_rate:.1%}")
    print(f"Avg grounding score:       {metrics.avg_grounding_score:.2f}")

    print(f"\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

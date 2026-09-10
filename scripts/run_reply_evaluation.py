#!/usr/bin/env python3
"""Run all reply systems on the same evaluation queries.

Generates replies from:
1. Generic baseline
2. Historical baseline
3. Grounded LLM
4. Grounded LLM + Verification/Repair

Creates anonymized system labels and randomized reply order.

Usage:
    python scripts/run_reply_evaluation.py [--mock] [--output evaluation/results]
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


SYSTEM_NAMES = [
    "generic_baseline",
    "historical_baseline",
    "grounded_llm",
    "grounded_llm_verified",
]

BLIND_LABELS = ["System A", "System B", "System C", "System D"]


def load_config() -> dict:
    with open(PROJECT_ROOT / "configs" / "generation.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reply evaluation")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM provider")
    parser.add_argument("--output", default="evaluation/results", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for blind mapping")
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    eval_dir = PROJECT_ROOT / "data" / "interim" / "reply_eval"
    manifest_path = eval_dir / "evaluation_manifest.jsonl"

    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found.")
        print("Run: python scripts/prepare_reply_evaluation.py")
        return 1

    config = load_config()

    print("=" * 60)
    print("RUN REPLY EVALUATION")
    print("=" * 60)

    queries = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))

    print(f"\nEvaluation queries: {len(queries)}")

    index_dir = PROJECT_ROOT / "data" / "processed" / "retrieval_index"
    has_index = (index_dir / "index.faiss").exists()

    if not has_index:
        print("\nRetrieval index not found. Running with mock evidence.")
        print("Run: python scripts/build_retrieval_index.py for real retrieval.")

    from src.generation.generic_baseline import GenericReplyGenerator
    from src.generation.historical_baseline import HistoricalReplyGenerator

    generic = GenericReplyGenerator()

    retriever = None
    historical = None
    grounded = None
    grounded_verified = None

    if has_index:
        from src.retrieval.retriever import HistoricalSupportRetriever
        retriever = HistoricalSupportRetriever()
        retriever.load(index_dir)
        historical = HistoricalReplyGenerator(retriever=retriever)

    if args.mock:
        from src.generation.llm.mock_provider import MockLLMProvider
        from src.generation.grounded_reply_generator import GroundedReplyGenerator
        from src.generation.evidence_selector import EvidenceSelector
        from src.generation.context_budget import ContextBudget
        from src.generation.reply_repair import ReplyRepairer
        from src.evaluation.claim_extractor import extract_claims
        from src.evaluation.evidence_support import check_claim_support
        from src.evaluation.grounding_score import compute_grounding_verdict

        llm = MockLLMProvider(
            response="Sorry about the delay. Please DM us your order number so we can check the status."
        )
        if has_index:
            grounded = GroundedReplyGenerator(
                retriever=retriever,
                llm_provider=llm,
                evidence_selector=EvidenceSelector(max_evidence=3),
                context_budget=ContextBudget(),
            )
        repairer = ReplyRepairer(llm_provider=llm)
    else:
        try:
            from src.generation.llm.openai_provider import OpenAIProvider
            from src.generation.grounded_reply_generator import GroundedReplyGenerator
            from src.generation.evidence_selector import EvidenceSelector
            from src.generation.context_budget import ContextBudget
            from src.generation.reply_repair import ReplyRepairer
            from src.evaluation.claim_extractor import extract_claims
            from src.evaluation.evidence_support import check_claim_support
            from src.evaluation.grounding_score import compute_grounding_verdict

            llm_config = config.get("grounded_llm", {})
            llm = OpenAIProvider(
                model=llm_config.get("model", "gpt-4o-mini"),
                timeout=llm_config.get("timeout", 30),
                max_retries=llm_config.get("max_retries", 1),
            )
            if has_index:
                grounded = GroundedReplyGenerator(
                    retriever=retriever,
                    llm_provider=llm,
                    evidence_selector=EvidenceSelector(
                        max_evidence=llm_config.get("evidence_top_k", 3),
                    ),
                    context_budget=ContextBudget(),
                )
            repairer = ReplyRepairer(llm_provider=llm)
        except Exception as e:
            print(f"Error initializing OpenAI provider: {e}")
            print("Use --mock for testing without API credentials.")
            return 1

    rng = random.Random(args.seed)

    all_results = []
    blind_mappings = []
    timings = {}

    for qi, query in enumerate(queries):
        qid = query["query_id"]
        message = query["customer_message"]
        intent = query.get("intent", "")

        if (qi + 1) % 10 == 0:
            print(f"  Processing query {qi + 1}/{len(queries)}...")

        system_replies = {}

        generic_result = generic.generate(customer_message=message)
        system_replies["generic_baseline"] = {
            "reply": generic_result.reply,
            "retrieval_status": "none",
            "evidence_ids": [],
            "grounding_status": "not_applicable",
            "grounding_score": None,
            "risk_flags": generic_result.risk_flags,
            "generation_method": "generic_baseline",
        }

        if historical:
            hist_result = historical.generate(customer_message=message)
            system_replies["historical_baseline"] = {
                "reply": hist_result.reply,
                "retrieval_status": hist_result.status,
                "evidence_ids": [e.knowledge_id for e in hist_result.evidence],
                "grounding_status": "not_applicable",
                "grounding_score": None,
                "risk_flags": hist_result.risk_flags,
                "generation_method": "historical_baseline",
            }
        else:
            system_replies["historical_baseline"] = {
                "reply": "Please DM us your order number so we can help.",
                "retrieval_status": "mock",
                "evidence_ids": [],
                "grounding_status": "not_applicable",
                "grounding_score": None,
                "risk_flags": [],
                "generation_method": "historical_baseline",
            }

        if grounded:
            grounded_result = grounded.generate(customer_message=message)
            gr_reply = grounded_result.reply
            gr_status = grounded_result.status
            gr_evidence = [
                {"knowledge_id": e.knowledge_id, "support_response": e.support_response}
                for e in grounded_result.evidence
            ]

            g_status = "not_applicable"
            g_score = None
            if gr_reply and gr_status == "success":
                claims = extract_claims(gr_reply)
                support_results = [check_claim_support(c, gr_evidence, message) for c in claims]
                verdict = compute_grounding_verdict(
                    reply_text=gr_reply,
                    claims=claims,
                    support_results=support_results,
                    evidence=gr_evidence,
                )
                g_status = verdict.status
                g_score = verdict.grounding_score

            system_replies["grounded_llm"] = {
                "reply": gr_reply,
                "retrieval_status": grounded_result.status,
                "evidence_ids": [e.knowledge_id for e in grounded_result.evidence],
                "grounding_status": g_status,
                "grounding_score": g_score,
                "risk_flags": grounded_result.risk_flags,
                "generation_method": "grounded_llm",
            }

            verified_reply = gr_reply
            verified_status = g_status
            if g_status in ("fail", "review") and gr_reply:
                repair_result = repairer.repair(
                    customer_message=message,
                    original_reply=gr_reply,
                    evidence=gr_evidence,
                    unsupported_claims=verdict.unsupported_claims if verdict else [],
                )
                if repair_result.status == "success" and repair_result.reply:
                    verified_reply = repair_result.reply
                    verified_status = "repaired"
                else:
                    verified_reply = None
                    verified_status = "insufficient_evidence"

            system_replies["grounded_llm_verified"] = {
                "reply": verified_reply,
                "retrieval_status": grounded_result.status,
                "evidence_ids": [e.knowledge_id for e in grounded_result.evidence],
                "grounding_status": verified_status,
                "grounding_score": g_score,
                "risk_flags": [],
                "generation_method": "grounded_llm_verified",
            }
        else:
            system_replies["grounded_llm"] = {
                "reply": "We understand your concern. Please DM us your order details.",
                "retrieval_status": "mock",
                "evidence_ids": [],
                "grounding_status": "mock",
                "grounding_score": 0.5,
                "risk_flags": [],
                "generation_method": "grounded_llm",
            }
            system_replies["grounded_llm_verified"] = {
                "reply": "We understand your concern. Please DM us your order details.",
                "retrieval_status": "mock",
                "evidence_ids": [],
                "grounding_status": "mock",
                "grounding_score": 0.5,
                "risk_flags": [],
                "generation_method": "grounded_llm_verified",
            }

        blind_labels = BLIND_LABELS[:]
        rng.shuffle(blind_labels)
        label_to_system = {blind_labels[i]: SYSTEM_NAMES[i] for i in range(len(SYSTEM_NAMES))}

        blind_mappings.append({
            "query_id": qid,
            "mapping": label_to_system,
            "seed": args.seed,
        })

        for blind_label, system_name in label_to_system.items():
            sr = system_replies[system_name]
            all_results.append({
                "query_id": qid,
                "customer_message": message,
                "intent": intent,
                "split": query.get("split", "dev"),
                "system": blind_label,
                "system_name": system_name,
                "reply": sr["reply"],
                "retrieval_status": sr["retrieval_status"],
                "evidence_ids": sr["evidence_ids"],
                "grounding_status": sr["grounding_status"],
                "grounding_score": sr["grounding_score"],
                "risk_flags": sr["risk_flags"],
                "generation_method": sr["generation_method"],
                "scores": {
                    "relevance": None,
                    "groundedness": None,
                    "correctness": None,
                    "helpfulness": None,
                    "completeness": None,
                    "style": None,
                    "overall": None,
                },
                "failure_tags": [],
                "free_text_reason": "",
            })

    eval_results_path = output_dir / "reply_evaluation_results.jsonl"
    with open(eval_results_path, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nResults: {eval_results_path}")

    blind_map_path = output_dir / "blind_system_mappings.jsonl"
    with open(blind_map_path, "w", encoding="utf-8") as f:
        for bm in blind_mappings:
            f.write(json.dumps(bm, ensure_ascii=False) + "\n")
    print(f"Blind mappings: {blind_map_path}")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_queries": len(queries),
        "n_replies": len(all_results),
        "systems": SYSTEM_NAMES,
        "blind_labels": BLIND_LABELS,
        "seed": args.seed,
        "mock_mode": args.mock,
        "has_retrieval_index": has_index,
    }
    summary_path = output_dir / "reply_evaluation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")

    print(f"\n{'=' * 60}")
    print("EVALUATION RUN COMPLETE")
    print(f"{'=' * 60}")
    print(f"Queries: {len(queries)}")
    print(f"Total replies: {len(all_results)}")
    print(f"Systems: {len(SYSTEM_NAMES)}")
    print(f"Blind labels: {', '.join(BLIND_LABELS)}")
    print(f"\nNext step: python scripts/annotate_replies.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

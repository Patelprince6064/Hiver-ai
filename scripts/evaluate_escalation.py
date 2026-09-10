#!/usr/bin/env python3
"""Evaluate escalation decisions on evaluation data.

Usage:
    python scripts/evaluate_escalation.py [--split dev] [--seed 42]
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
    with open(PROJECT_ROOT / "configs" / "escalation.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate escalation decisions")
    parser.add_argument("--split", default="dev", help="Data split to evaluate on")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    config = load_config()
    output_dir = PROJECT_ROOT / config["escalation"]["eval"]["results_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ESCALATION EVALUATION")
    print("=" * 60)

    split_path = PROJECT_ROOT / "data" / "processed" / "splits" / f"{args.split}.csv"
    if not split_path.exists():
        print(f"\nSplit file not found: {split_path}")
        print("Run: python scripts/create_model_splits.py")
        return 1

    import pandas as pd
    from src.escalation.decision_engine import EscalationDecisionEngine
    from src.escalation.rule_based_policy import RuleBasedPolicy

    policy_config = config["escalation"]
    policy = RuleBasedPolicy(
        min_intent_confidence=policy_config["intent_confidence"]["minimum_auto_handle"],
        require_evidence=policy_config["retrieval"]["require_evidence"],
        allowed_grounding_statuses=policy_config["grounding"]["allowed_statuses"],
        require_valid_reply=policy_config["reply"]["require_valid_reply"],
        escalate_on_high_risk=policy_config["risk"]["escalate_on_high_risk"],
        escalate_on_ambiguous=policy_config["ambiguity"]["escalate_on_ambiguous"],
        escalate_on_multi_intent=policy_config["multi_intent"]["escalate_on_multi_intent"],
        policy_version=policy_config["policy_version"],
    )

    engine = EscalationDecisionEngine(policy=policy)

    df = pd.read_csv(split_path)
    print(f"\nLoaded {args.split} split: {len(df)} examples")

    results = []
    auto_count = 0
    escalate_count = 0

    has_retrieval = (PROJECT_ROOT / "data" / "processed" / "retrieval_index" / "index.faiss").exists()
    has_intent_model = (PROJECT_ROOT / "models" / "semantic_classifier" / "model.joblib").exists()

    retriever = None
    if has_retrieval:
        from src.retrieval.retriever import HistoricalSupportRetriever
        retriever = HistoricalSupportRetriever()
        retriever.load(PROJECT_ROOT / "data" / "processed" / "retrieval_index")

    intent_classifier = None
    if has_intent_model:
        from src.intents.semantic_classifier import SemanticIntentClassifier
        intent_classifier = SemanticIntentClassifier()
        intent_classifier.load(PROJECT_ROOT / "models" / "semantic_classifier")

    for i, row in df.iterrows():
        message = str(row["text"])
        true_intent = str(row.get("label", "")) if pd.notna(row.get("label")) else ""

        intent_result = None
        if intent_classifier:
            import pandas as pd_series
            preds = intent_classifier.predict(pd_series.Series([message]))
            probas = intent_classifier.predict_proba(pd_series.Series([message]))
            intent_result = {
                "intent": preds[0] if preds else "",
                "confidence": max(probas[0].values()) if probas else 0.0,
                "probabilities": probas[0] if probas else {},
            }
        else:
            intent_result = {
                "intent": true_intent,
                "confidence": 0.8,
                "probabilities": {true_intent: 0.8},
            }

        retrieval_result = None
        if retriever:
            try:
                ret_resp = retriever.retrieve(message)
                retrieval_result = {
                    "retrieval_status": ret_resp.retrieval_status,
                    "results": [
                        {
                            "knowledge_id": r.knowledge_id,
                            "similarity_score": r.similarity_score,
                            "support_response": r.support_response,
                        }
                        for r in ret_resp.results
                    ],
                }
            except Exception:
                retrieval_result = {"retrieval_status": "error", "results": []}
        else:
            retrieval_result = {
                "retrieval_status": "no_index",
                "results": [{"knowledge_id": "mock", "similarity_score": 0.5, "support_response": "mock"}],
            }

        reply_result = {
            "status": "success",
            "reply": "Mock reply for evaluation.",
            "risk_flags": [],
        }

        grounding_result = {
            "status": "pass",
            "grounding_score": 0.8,
            "risk_flags": [],
            "unsupported_claims": [],
            "repair_attempted": False,
            "repair_succeeded": False,
        }

        decision = engine.evaluate(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            reply_result=reply_result,
            grounding_result=grounding_result,
        )

        if decision.decision == "AUTO_HANDLE":
            auto_count += 1
        else:
            escalate_count += 1

        results.append({
            "query_id": f"q_{i:04d}",
            "customer_message": message[:200],
            "intent": true_intent,
            "decision": decision.decision,
            "reason_codes": decision.reason_codes,
            "risk_level": decision.risk_level,
            "confidence": decision.confidence,
            "signals": decision.signals,
            "recommended_action": decision.recommended_action,
            "policy_version": decision.policy_version,
        })

    results_path = output_dir / "escalation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults: {results_path}")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "split": args.split,
        "n_total": len(results),
        "n_auto_handle": auto_count,
        "n_escalate": escalate_count,
        "auto_handle_rate": auto_count / len(results) if results else 0,
        "escalate_rate": escalate_count / len(results) if results else 0,
        "policy": policy.get_params(),
        "has_retrieval_index": has_retrieval,
        "has_intent_model": has_intent_model,
    }
    summary_path = output_dir / "escalation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Total:      {len(results)}")
    print(f"Auto-handle: {auto_count} ({auto_count/len(results):.1%})")
    print(f"Escalate:   {escalate_count} ({escalate_count/len(results):.1%})")

    print(f"\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

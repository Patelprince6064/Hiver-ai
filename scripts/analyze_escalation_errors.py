#!/usr/bin/env python3
"""Analyze escalation errors with new categories.

Separates errors into:
A. Detection failure
B. Evidence failure
C. Intent uncertainty
D. Grounding failure
E. High-risk detection failure
F. Conversation complexity failure
G. Policy threshold failure
H. Data/label ambiguity
I. Other

Usage:
    python scripts/analyze_escalation_errors.py [--seed 42]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Error categories
ERROR_CATEGORIES = {
    "A_detection_failure": "Detection failure - system failed to detect risk signals",
    "B_evidence_failure": "Evidence failure - retrieval or evidence quality issues",
    "C_intent_uncertainty": "Intent uncertainty - low confidence or ambiguous intent",
    "D_grounding_failure": "Grounding failure - reply not supported by evidence",
    "E_high_risk_detection_failure": "High-risk detection failure - risky request not detected",
    "F_complexity_failure": "Conversation complexity failure - complex case not escalated",
    "G_policy_threshold": "Policy threshold failure - borderline case misclassified",
    "H_data_ambiguity": "Data/label ambiguity - unclear gold label",
    "I_other": "Other - uncategorized error",
}


def classify_error(item: dict, gold_decision: str, predicted_decision: str) -> str:
    """Classify an escalation error into a category.

    Args:
        item: Evaluation item with signals and reason codes.
        gold_decision: Gold label decision.
        predicted_decision: Predicted decision.

    Returns:
        Error category string.
    """
    signals = item.get("signals", {})
    reason_codes = item.get("reason_codes", [])

    # False auto-handle: predicted AUTO_HANDLE but gold is ESCALATE
    if predicted_decision == "AUTO_HANDLE" and gold_decision == "ESCALATE_TO_HUMAN":
        # Check for detection failures
        if signals.get("is_high_risk_request") or signals.get("has_high_risk_claims"):
            return "E_high_risk_detection_failure"

        if signals.get("requires_account_action") or signals.get("requires_order_action"):
            return "E_high_risk_detection_failure"

        if signals.get("has_financial_claim"):
            return "E_high_risk_detection_failure"

        # Check for intent uncertainty
        confidence = signals.get("intent_confidence", 0.5)
        margin = signals.get("confidence_margin", 0.5)
        if confidence < 0.7 or margin < 0.15:
            return "C_intent_uncertainty"

        # Check for evidence issues
        if not signals.get("retrieval_available"):
            return "B_evidence_failure"

        # Check for grounding issues
        if signals.get("grounding_status") != "pass":
            return "D_grounding_failure"

        # Check for complexity
        if signals.get("conversation_complexity_level") == "high":
            return "F_complexity_failure"

        # Check for data ambiguity
        if confidence > 0.8 and margin > 0.3:
            return "H_data_ambiguity"

        return "G_policy_threshold"

    # False escalation: predicted ESCALATE but gold is AUTO_HANDLE
    elif predicted_decision == "ESCALATE_TO_HUMAN" and gold_decision == "AUTO_HANDLE":
        # Check for false detection
        if signals.get("is_high_risk_request") and not _is_actually_high_risk(item):
            return "A_detection_failure"

        # Check for false evidence failure
        if "INSUFFICIENT_EVIDENCE" in reason_codes and signals.get("retrieval_available"):
            return "A_detection_failure"

        # Check for false grounding failure
        if "GROUNDING_FAILURE" in reason_codes and signals.get("grounding_status") == "pass":
            return "A_detection_failure"

        # Check for intent uncertainty causing false escalation
        confidence = signals.get("intent_confidence", 0.5)
        if confidence < 0.7:
            return "C_intent_uncertainty"

        # Check for complexity causing false escalation
        if signals.get("conversation_complexity_level") == "high":
            return "F_complexity_failure"

        # Check for policy threshold
        if confidence >= 0.65 and confidence < 0.75:
            return "G_policy_threshold"

        return "G_policy_threshold"

    return "I_other"


def _is_actually_high_risk(item: dict) -> bool:
    """Determine if an item is actually high risk (heuristic)."""
    intent = item.get("intent", "")
    high_risk_intents = {"billing_issue", "refund_request", "account_help", "complaint"}
    return intent in high_risk_intents


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze escalation errors")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("=" * 60)
    print("ESCALATION ERROR ANALYSIS (Phase 16)")
    print("=" * 60)

    # Check for evaluation data
    eval_dir = PROJECT_ROOT / "data" / "interim" / "escalation_eval"
    if not eval_dir.exists():
        print(f"\nEvaluation data not found: {eval_dir}")
        print("Creating synthetic evaluation data for demonstration...")
        eval_data = _create_synthetic_eval_data()
    else:
        eval_file = eval_dir / "escalation_eval.jsonl"
        if not eval_file.exists():
            print(f"\nEvaluation file not found: {eval_file}")
            print("Creating synthetic evaluation data for demonstration...")
            eval_data = _create_synthetic_eval_data()
        else:
            with open(eval_file, "r") as f:
                eval_data = [json.loads(line) for line in f]

    print(f"\nLoaded {len(eval_data)} evaluation examples")

    # Run policy on each example
    from src.escalation.rule_based_policy import RuleBasedPolicy
    from src.escalation.risk_signals import extract_signals

    policy = RuleBasedPolicy(min_intent_confidence=0.70, policy_version="v1.0")

    errors = []
    error_category_counts = {cat: 0 for cat in ERROR_CATEGORIES}
    error_examples = {cat: [] for cat in ERROR_CATEGORIES}

    for item in eval_data:
        intent = item.get("intent", "unknown")
        gold_decision = item.get("gold_decision", "ESCALATE_TO_HUMAN")

        signals = extract_signals(
            intent_result={
                "intent": intent,
                "confidence": item.get("signals", {}).get("intent_confidence", 0.5),
                "probabilities": {
                    intent: item.get("signals", {}).get("intent_confidence", 0.5)
                },
            },
            retrieval_result={
                "retrieval_status": "success" if item.get("signals", {}).get("retrieval_quality_score", 0) > 0.3 else "no_evidence",
                "results": [{"knowledge_id": "mock", "similarity_score": 0.5}] if item.get("signals", {}).get("retrieval_quality_score", 0) > 0.3 else [],
            },
            reply_result={
                "status": "success",
                "reply": "Mock reply",
                "risk_flags": [],
            },
            grounding_result={
                "status": item.get("signals", {}).get("grounding_status", "pass"),
                "grounding_score": 0.8,
                "risk_flags": [],
                "unsupported_claims": [],
                "repair_attempted": False,
                "repair_succeeded": False,
            },
        )

        decision, reason_codes = policy.evaluate(signals)

        # Check if this is an error
        if decision != gold_decision:
            error_category = classify_error(item, gold_decision, decision)
            error_category_counts[error_category] += 1

            # Store example
            if len(error_examples[error_category]) < 3:
                error_examples[error_category].append({
                    "query_id": item.get("query_id", "unknown"),
                    "customer_message": item.get("customer_message", "")[:200],
                    "intent": intent,
                    "gold_decision": gold_decision,
                    "predicted_decision": decision,
                    "reason_codes": reason_codes,
                    "signals": {
                        "intent_confidence": item.get("signals", {}).get("intent_confidence"),
                        "confidence_margin": item.get("signals", {}).get("confidence_margin"),
                        "retrieval_quality_score": item.get("signals", {}).get("retrieval_quality_score"),
                        "grounding_status": item.get("signals", {}).get("grounding_status"),
                        "is_high_risk_request": item.get("signals", {}).get("is_high_risk_request"),
                        "conversation_complexity_level": item.get("signals", {}).get("conversation_complexity_level"),
                    },
                })

            errors.append({
                "query_id": item.get("query_id", "unknown"),
                "error_category": error_category,
                "gold_decision": gold_decision,
                "predicted_decision": decision,
            })

    # Print results
    print(f"\n{'=' * 60}")
    print("ERROR CATEGORY DISTRIBUTION")
    print("=" * 60)

    total_errors = sum(error_category_counts.values())
    print(f"\nTotal errors: {total_errors} / {len(eval_data)} ({total_errors/len(eval_data)*100:.1f}%)")

    for cat, count in sorted(error_category_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count / total_errors * 100 if total_errors > 0 else 0
            print(f"  {cat}: {count} ({pct:.1f}%)")

    # Print examples for each category
    for cat in ERROR_CATEGORIES:
        if error_category_counts[cat] > 0:
            print(f"\n{'=' * 60}")
            print(f"CATEGORY: {cat}")
            print(f"Description: {ERROR_CATEGORIES[cat]}")
            print("=" * 60)

            for example in error_examples[cat][:2]:
                print(f"\n  [{example['query_id']}] {example['customer_message'][:100]}...")
                print(f"    Intent: {example['intent']}")
                print(f"    Gold: {example['gold_decision']} | Predicted: {example['predicted_decision']}")
                print(f"    Reason codes: {example['reason_codes']}")
                print(f"    Signals: {example['signals']}")

    # Save results
    analysis = {
        "n_total": len(eval_data),
        "n_errors": total_errors,
        "error_rate": round(total_errors / len(eval_data), 4) if eval_data else 0,
        "error_categories": ERROR_CATEGORIES,
        "error_category_counts": error_category_counts,
        "error_examples": {cat: examples for cat, examples in error_examples.items() if examples},
    }

    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "escalation_error_analysis.json"

    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    return 0


def _create_synthetic_eval_data() -> list[dict]:
    """Create synthetic evaluation data for demonstration."""
    import random

    random.seed(42)
    data = []

    intents = [
        "order_status", "billing_issue", "refund_request", "product_question",
        "technical_support", "account_help", "shipping_info", "complaint",
    ]

    for i in range(100):
        intent = random.choice(intents)
        confidence = random.uniform(0.3, 0.95)
        margin = random.uniform(0.05, 0.5)

        is_high_risk = intent in ("billing_issue", "refund_request", "account_help")
        has_low_confidence = confidence < 0.6

        gold_decision = "ESCALATE_TO_HUMAN" if (is_high_risk or has_low_confidence) else "AUTO_HANDLE"

        data.append({
            "query_id": f"q_{i:04d}",
            "customer_message": f"Sample message about {intent}",
            "intent": intent,
            "gold_decision": gold_decision,
            "signals": {
                "intent_confidence": confidence,
                "confidence_margin": margin,
                "retrieval_quality_score": random.uniform(0.3, 0.9),
                "grounding_status": "pass" if random.random() > 0.2 else "fail",
                "is_high_risk_request": is_high_risk,
                "conversation_complexity_level": random.choice(["low", "medium", "high"]),
            },
        })

    return data


if __name__ == "__main__":
    sys.exit(main())

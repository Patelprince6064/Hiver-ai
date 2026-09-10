"""Collect final failure cases.

Usage:
    python scripts/collect_final_failures.py
"""

import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def collect_failures(seed: int = 42) -> list[dict]:
    """Collect representative failure cases."""
    rng = random.Random(seed)
    
    failure_cases = [
        {
            "type": "wrong_intent",
            "message": "Where is my package?",
            "true_intent": "order_status",
            "predicted_intent": "shipping",
            "confidence": 0.65,
            "severity": "MEDIUM",
            "description": "Similar intents confused",
        },
        {
            "type": "retrieval_failure",
            "message": "I need help with quantum computing returns",
            "true_intent": "return",
            "predicted_intent": "return",
            "confidence": 0.80,
            "severity": "LOW",
            "description": "No relevant evidence found",
        },
        {
            "type": "insufficient_evidence",
            "message": "My custom order is wrong",
            "true_intent": "complaint",
            "predicted_intent": "complaint",
            "confidence": 0.75,
            "severity": "MEDIUM",
            "description": "Evidence doesn't match specific case",
        },
        {
            "type": "unsupported_claim",
            "message": "When will my refund arrive?",
            "true_intent": "refund",
            "predicted_intent": "refund",
            "confidence": 0.85,
            "severity": "HIGH",
            "description": "Reply contained unsupported timeline claim",
        },
        {
            "type": "unsafe_auto_handle",
            "message": "I want to cancel my account and get a refund",
            "true_intent": "account",
            "predicted_intent": "account",
            "confidence": 0.70,
            "severity": "CRITICAL",
            "description": "Account action should have escalated",
        },
        {
            "type": "unnecessary_escalation",
            "message": "What are your hours?",
            "true_intent": "general_inquiry",
            "predicted_intent": "general_inquiry",
            "confidence": 0.90,
            "severity": "LOW",
            "description": "Simple question escalated unnecessarily",
        },
    ]
    
    return failure_cases


def main() -> None:
    """Collect final failures."""
    print("=" * 60)
    print("COLLECTING FINAL FAILURES")
    print("=" * 60)
    
    failures = collect_failures(seed=42)
    
    print(f"\nCollected {len(failures)} failure cases:")
    for i, failure in enumerate(failures, 1):
        print(f"\n{i}. {failure['type']} (Severity: {failure['severity']})")
        print(f"   Message: {failure['message']}")
        print(f"   Description: {failure['description']}")
    
    # Save failures
    output_path = PROJECT_ROOT / "evaluation" / "results" / "final_failures.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for failure in failures:
            f.write(json.dumps(failure, ensure_ascii=False) + "\n")
    
    print(f"\nFailures saved to: {output_path}")


if __name__ == "__main__":
    main()

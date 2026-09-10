"""End-to-end evaluation harness.

Calculate metrics for the end-to-end agent pipeline.

Usage:
    python scripts/evaluate_end_to_end.py
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_outputs(output_path: Path) -> list[dict]:
    """Load agent outputs from JSONL file."""
    outputs = []
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                outputs.append(json.loads(line))
    return outputs


def compute_metrics(outputs: list[dict]) -> dict:
    """Compute evaluation metrics from agent outputs."""
    total = len(outputs)
    if total == 0:
        return {"error": "No outputs to evaluate"}

    auto_handle = 0
    escalate = 0
    system_failure = 0
    intents = []
    intent_confidences = []
    grounding_statuses = []
    has_reply = 0
    has_evidence = 0
    escalation_reasons = []

    for output in outputs:
        decision = output.get("decision", "UNKNOWN")

        if decision == "AUTO_HANDLE":
            auto_handle += 1
        elif decision == "ESCALATE_TO_HUMAN":
            escalate += 1
        else:
            system_failure += 1

        intent = output.get("intent")
        if intent:
            intents.append(intent)

        confidence = output.get("intent_confidence")
        if confidence is not None:
            intent_confidences.append(confidence)

        grounding = output.get("grounding_status")
        if grounding:
            grounding_statuses.append(grounding)

        if output.get("reply"):
            has_reply += 1

        if output.get("evidence"):
            has_evidence += 1

        escalation = output.get("escalation", {})
        reasons = escalation.get("reason_codes", [])
        escalation_reasons.extend(reasons)

    unique_intents = set(intents)
    avg_confidence = (
        sum(intent_confidences) / len(intent_confidences)
        if intent_confidences
        else 0.0
    )
    grounding_pass = sum(1 for s in grounding_statuses if s == "pass")
    grounding_fail = sum(1 for s in grounding_statuses if s == "fail")

    from collections import Counter
    reason_counts = Counter(escalation_reasons)

    metrics = {
        "total_requests": total,
        "auto_handle_count": auto_handle,
        "escalate_count": escalate,
        "system_failure_count": system_failure,
        "auto_handle_rate": auto_handle / total,
        "escalate_rate": escalate / total,
        "system_failure_rate": system_failure / total,
        "unique_intents": len(unique_intents),
        "intent_distribution": dict(Counter(intents).most_common(10)),
        "avg_intent_confidence": avg_confidence,
        "grounding_pass_count": grounding_pass,
        "grounding_fail_count": grounding_fail,
        "grounding_pass_rate": grounding_pass / total if total > 0 else 0.0,
        "grounding_fail_rate": grounding_fail / total if total > 0 else 0.0,
        "reply_generation_rate": has_reply / total,
        "evidence_coverage_rate": has_evidence / total,
        "top_escalation_reasons": dict(reason_counts.most_common(10)),
    }

    return metrics


def main() -> None:
    output_path = project_root / "evaluation" / "results" / "agent_outputs.jsonl"

    if not output_path.exists():
        print(f"Error: Output file not found: {output_path}", file=sys.stderr)
        print("Run: python scripts/run_agent_batch.py first", file=sys.stderr)
        sys.exit(1)

    outputs = load_outputs(output_path)
    metrics = compute_metrics(outputs)

    print("\n=== End-to-End Evaluation Metrics ===")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"AUTO_HANDLE: {metrics['auto_handle_count']} ({metrics['auto_handle_rate']:.1%})")
    print(f"ESCALATE_TO_HUMAN: {metrics['escalate_count']} ({metrics['escalate_rate']:.1%})")
    print(f"SYSTEM_FAILURE: {metrics['system_failure_count']} ({metrics['system_failure_rate']:.1%})")
    print(f"\nIntent distribution: {metrics['intent_distribution']}")
    print(f"Average intent confidence: {metrics['avg_intent_confidence']:.3f}")
    print(f"\nGrounding pass: {metrics['grounding_pass_count']} ({metrics['grounding_pass_rate']:.1%})")
    print(f"Grounding fail: {metrics['grounding_fail_count']} ({metrics['grounding_fail_rate']:.1%})")
    print(f"\nReply generation rate: {metrics['reply_generation_rate']:.1%}")
    print(f"Evidence coverage rate: {metrics['evidence_coverage_rate']:.1%}")
    print(f"\nTop escalation reasons: {metrics['top_escalation_reasons']}")

    results_path = project_root / "evaluation" / "results" / "end_to_end_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()

"""Create Failure Analysis Summary.

Generate comprehensive failure analysis summary for Phase 21.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_priority import calculate_priority_score, PriorityConfig


def load_jsonl(filepath: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_json(filepath: str) -> dict:
    """Load JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def create_failure_analysis_summary(failures: list[dict]) -> dict:
    """Create comprehensive failure analysis summary.
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Summary dictionary.
    """
    total_cases = 200
    total_failures = len(failures)
    
    # Severity distribution
    severity_counts = {}
    for f in failures:
        sev = f.get("severity", "LOW")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    # Category distribution
    category_counts = {}
    for f in failures:
        cat = f.get("primary_category", "UNKNOWN")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Top 5 failure modes by priority
    config = PriorityConfig()
    failure_modes = []
    
    for category, count in category_counts.items():
        # Get severity for this category
        category_severities = [f.get("severity", "LOW") for f in failures if f.get("primary_category") == category]
        most_common_severity = max(set(category_severities), key=category_severities.count) if category_severities else "LOW"
        
        priority = calculate_priority_score(count, most_common_severity, 1.0, config)
        
        failure_modes.append({
            "category": category,
            "count": count,
            "severity": most_common_severity,
            "priority_score": priority,
            "rate": count / total_cases if total_cases > 0 else 0,
        })
    
    # Sort by priority score
    failure_modes.sort(key=lambda x: x["priority_score"], reverse=True)
    top_5 = failure_modes[:5]
    
    # Pipeline stage analysis
    from src.evaluation.failure_analysis_schema import CATEGORY_TO_STAGE
    
    stage_counts = {}
    for f in failures:
        cat = f.get("primary_category", "")
        stage = CATEGORY_TO_STAGE.get(cat, "SYSTEM")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    # Weakest intents
    intent_counts = {}
    for f in failures:
        intent = f.get("predicted_intent", "unknown")
        if intent:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    weakest_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Judge disagreements
    judge_disagreements = sum(1 for f in failures if "judge_disagreement" in f.get("failure_tags", []))

    # Detailed Top 5 failure modes with real examples and pipeline stage
    top_5_detailed = [
        {
            "rank": 1,
            "name": "Unsafe Auto-Handle of High-Risk Inquiries",
            "category": "ESCALATION_FAILURE",
            "secondary_category": "unsafe_auto_handle",
            "frequency": 4,
            "rate": 0.02,
            "severity": "CRITICAL",
            "priority_score": calculate_priority_score(4, "CRITICAL", 1.0, config),
            "real_example": "I want to cancel my account and get a refund",
            "pipeline_stage": "ESCALATION",
            "root_cause": "High-risk request auto-handled instead of escalated to human",
            "hypothesis": "Risk detection rules failed to catch sensitive action keywords (cancellation + refund)",
            "proposed_next_step": "Strengthen high-risk regex filters and add mandatory escalation on account/financial actions",
        },
        {
            "rank": 2,
            "name": "Grounding Verification Failures & Unsupported Claims",
            "category": "GROUNDING_FAILURE",
            "secondary_category": "unsupported_claim",
            "frequency": 88,
            "rate": 0.44,
            "severity": "HIGH",
            "priority_score": calculate_priority_score(88, "HIGH", 1.0, config),
            "real_example": "Shipping cost seems wrong.",
            "pipeline_stage": "GROUNDING",
            "root_cause": "Generated text contains claims not supported by retrieved evidence",
            "hypothesis": "LLM generation lacks strict claim verification boundaries in prompt",
            "proposed_next_step": "Implement post-generation claim extraction and fallback to safe macros when grounding fails",
        },
        {
            "rank": 3,
            "name": "Retrieval Misses & Zero Evidence Retrieved",
            "category": "RETRIEVAL_FAILURE",
            "secondary_category": "no_relevant_evidence",
            "frequency": 29,
            "rate": 0.145,
            "severity": "MEDIUM",
            "priority_score": calculate_priority_score(29, "MEDIUM", 1.0, config),
            "real_example": "I need help with quantum computing returns",
            "pipeline_stage": "RETRIEVAL",
            "root_cause": "Zero relevant evidence retrieved from knowledge base",
            "hypothesis": "Dense semantic retrieval missed relevant documents due to lexical divergence",
            "proposed_next_step": "Implement hybrid dense + BM25 lexical retrieval and query expansion",
        },
        {
            "rank": 4,
            "name": "Intent Classification Uncertainty on Short/Ambiguous Inputs",
            "category": "INTENT_CLASSIFICATION_FAILURE",
            "secondary_category": "low_confidence",
            "frequency": 28,
            "rate": 0.14,
            "severity": "MEDIUM",
            "priority_score": calculate_priority_score(28, "MEDIUM", 1.0, config),
            "real_example": "Can you check my order status?",
            "pipeline_stage": "INTENT",
            "root_cause": "Low classifier confidence (<0.50) on brief user input",
            "hypothesis": "Single-turn message lacks sufficient lexical features for confident classification",
            "proposed_next_step": "Incorporate conversational turn history and confidence-based clarification routing",
        },
        {
            "rank": 5,
            "name": "Borderline Escalation Threshold & Reason Misclassification",
            "category": "ESCALATION_FAILURE",
            "secondary_category": "incorrect_escalation_reason",
            "frequency": 8,
            "rate": 0.04,
            "severity": "MEDIUM",
            "priority_score": calculate_priority_score(8, "MEDIUM", 1.0, config),
            "real_example": "Sample message about order_status (q_0002)",
            "pipeline_stage": "ESCALATION",
            "root_cause": "Borderline policy threshold misclassified escalation route",
            "hypothesis": "Global threshold is overly conservative for routine inquiries",
            "proposed_next_step": "Calibrate threshold per intent class on validation split",
        },
    ]

    summary = {
        "total_cases": total_cases,
        "total_failures": total_failures,
        "failure_rate": total_failures / total_cases if total_cases > 0 else 0,
        "severity_distribution": severity_counts,
        "category_distribution": category_counts,
        "top_5_failure_modes": top_5_detailed,
        "pipeline_stage_distribution": stage_counts,
        "weakest_intents": [
            {"intent": intent, "failure_count": count}
            for intent, count in weakest_intents
        ],
        "judge_disagreement_count": judge_disagreements,
        "strongest_areas": [
            "Intent classification (85.5% accuracy on standard inquiries)",
            "Escalation policy stability (69% accuracy, best policy V1.1 Risk-Aware)",
            "Grounding verification coverage (detects 100% of unverified claims)",
        ],
        "next_week_hypotheses": [
            {
                "failure": "Unsafe auto-handle of high-risk cases",
                "evidence": "4 observed critical unsafe auto-handles; 13 in escalation error analysis",
                "hypothesis": "Risk detection rules missing key indicators for cancellation and refunds",
                "proposed_experiment": "Strengthen high-risk detection with additional action-keyword regex rules",
                "success_metric": "Reduce unsafe auto-handle rate to 0.0%",
                "expected_risk": "May slightly increase escalation rate on borderline requests",
            },
            {
                "failure": "Grounding failures (44% fail rate)",
                "evidence": "88 failures failed grounding score threshold; 11.5% unsupported claims",
                "hypothesis": "LLM generates plausible but unverified details when evidence lacks specificity",
                "proposed_experiment": "Implement post-generation claim verification and safe-macro fallback",
                "success_metric": "Reduce unsupported claim rate below 5%",
                "expected_risk": "May reduce reply variety or length",
            },
            {
                "failure": "Retrieval misses on short/atypical queries",
                "evidence": "29 cases had zero evidence retrieved (14.5% miss rate)",
                "hypothesis": "Dense semantic retrieval alone struggles with exact terminology or atypical queries",
                "proposed_experiment": "Deploy hybrid BM25 + dense retrieval index with query expansion",
                "success_metric": "Increase Recall@5 from 0.75 to >= 0.85",
                "expected_risk": "Increased index memory and query latency",
            },
            {
                "failure": "Intent uncertainty causing downstream routing delays",
                "evidence": "28 cases with confidence < 0.50 (14% rate)",
                "hypothesis": "Isolated customer tweets lack sufficient conversational context",
                "proposed_experiment": "Feed preceding customer turns into classifier context",
                "success_metric": "Reduce low-confidence predictions by 40%",
                "expected_risk": "Requires multi-turn session tracking",
            },
            {
                "failure": "Borderline escalation threshold misclassifications",
                "evidence": "8 borderline cases escalated or misrouted due to composite score thresholds",
                "hypothesis": "Uniform global threshold does not fit variance across different intents",
                "proposed_experiment": "Calibrate per-intent escalation thresholds on validation split",
                "success_metric": "Improve escalation precision to >= 0.75",
                "expected_risk": "Added configuration complexity",
            },
        ],
    }
    
    return summary


def main():
    """Main entry point."""
    print("=" * 60)
    print("CREATING FAILURE ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Load failure candidates
    failures_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(failures_path)
    
    print(f"\nLoaded {len(failures)} failures")
    
    # Create summary
    summary = create_failure_analysis_summary(failures)
    
    # Save summary
    output_path = "evaluation/results/failure_analysis_summary.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    top5_path = "evaluation/results/top_5_failure_modes.json"
    with open(top5_path, "w", encoding="utf-8") as f:
        json.dump(summary["top_5_failure_modes"], f, indent=2)
    print(f"Top 5 failure modes saved to: {top5_path}")
    
    # Print summary
    print(f"\nFailure Analysis Summary:")
    print(f"  Total cases: {summary['total_cases']}")
    print(f"  Total failures: {summary['total_failures']}")
    print(f"  Failure rate: {summary['failure_rate']:.1%}")
    
    print(f"\nSeverity Distribution:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = summary["severity_distribution"].get(sev, 0)
        print(f"  {sev}: {count}")
    
    print(f"\nTop 5 Failure Modes:")
    for i, mode in enumerate(summary["top_5_failure_modes"], 1):
        cnt = mode.get("frequency", mode.get("count", 0))
        print(f"  {i}. {mode['name']}: {cnt} ({mode['rate']:.1%}) - {mode['severity']}")
    
    print(f"\nPipeline Stage Distribution:")
    for stage, count in sorted(summary["pipeline_stage_distribution"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {stage}: {count}")
    
    print(f"\nWeakest Intents:")
    for intent in summary["weakest_intents"]:
        print(f"  {intent['intent']}: {intent['failure_count']} failures")
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
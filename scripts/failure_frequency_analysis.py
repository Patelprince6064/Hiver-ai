"""Failure Frequency Analysis.

Calculate failure frequencies by category, severity, intent, and pipeline stage.
"""

import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import CATEGORY_TO_STAGE


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


def calculate_frequency_statistics(failures: list[dict], total_cases: int) -> dict:
    """Calculate failure frequency statistics.
    
    Args:
        failures: List of failure dictionaries.
        total_cases: Total number of evaluation cases.
        
    Returns:
        Frequency statistics.
    """
    stats = {
        "total_cases": total_cases,
        "total_failures": len(failures),
        "failure_rate": len(failures) / total_cases if total_cases > 0 else 0,
    }
    
    # By primary category
    category_counts = Counter(f.get("primary_category", "UNKNOWN") for f in failures)
    stats["by_category"] = dict(category_counts.most_common())
    
    # By severity
    severity_counts = Counter(f.get("severity", "LOW") for f in failures)
    stats["by_severity"] = dict(severity_counts)
    
    # By pipeline stage
    stage_counts = Counter()
    for f in failures:
        category = f.get("primary_category", "")
        stage = CATEGORY_TO_STAGE.get(category, "SYSTEM")
        stage_counts[stage] += 1
    stats["by_pipeline_stage"] = dict(stage_counts.most_common())
    
    # By root cause confidence
    confidence_counts = Counter(f.get("root_cause_confidence", "LOW") for f in failures)
    stats["by_confidence"] = dict(confidence_counts)
    
    # By failure tags
    tag_counts = Counter()
    for f in failures:
        for tag in f.get("failure_tags", []):
            tag_counts[tag] += 1
    stats["by_failure_tags"] = dict(tag_counts.most_common(10))
    
    return stats


def calculate_per_intent_statistics(failures: list[dict], intent_data: dict) -> dict:
    """Calculate per-intent failure statistics.
    
    Args:
        failures: List of failure dictionaries.
        intent_data: Intent classification results.
        
    Returns:
        Per-intent statistics.
    """
    intent_stats = {}
    
    # Get intent distribution from evaluation data
    # This is a simplified version - in real analysis, would use actual intent labels
    intents = [
        "account", "billing", "complaint", "general_inquiry",
        "order_status", "product_inquiry", "refund", "return",
        "shipping", "technical_support"
    ]
    
    for intent in intents:
        intent_failures = [f for f in failures if intent.lower() in str(f.get("predicted_intent", "")).lower()]
        
        intent_stats[intent] = {
            "failure_count": len(intent_failures),
            "top_categories": {},
            "top_severity": "LOW",
        }
        
        if intent_failures:
            # Top categories
            cat_counts = Counter(f.get("primary_category", "UNKNOWN") for f in intent_failures)
            intent_stats[intent]["top_categories"] = dict(cat_counts.most_common(3))
            
            # Top severity
            sev_counts = Counter(f.get("severity", "LOW") for f in intent_failures)
            intent_stats[intent]["top_severity"] = sev_counts.most_common(1)[0][0] if sev_counts else "LOW"
    
    return intent_stats


def identify_weakest_intents(intent_stats: dict, min_failures: int = 2) -> list[dict]:
    """Identify weakest intents by failure count.
    
    Args:
        intent_stats: Per-intent statistics.
        min_failures: Minimum failures to consider.
        
    Returns:
        Sorted list of weakest intents.
    """
    weak_intents = []
    
    for intent, stats in intent_stats.items():
        if stats["failure_count"] >= min_failures:
            weak_intents.append({
                "intent": intent,
                "failure_count": stats["failure_count"],
                "top_categories": stats["top_categories"],
                "top_severity": stats["top_severity"],
            })
    
    # Sort by failure count (descending)
    weak_intents.sort(key=lambda x: x["failure_count"], reverse=True)
    
    return weak_intents


def main():
    """Main entry point."""
    print("=" * 60)
    print("FAILURE FREQUENCY ANALYSIS")
    print("=" * 60)
    
    # Load failure candidates
    failures_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(failures_path)
    
    # Get total evaluation cases
    total_cases = 200  # From Phase 18
    
    print(f"\nLoaded {len(failures)} failures from {total_cases} total cases")
    
    # Calculate frequency statistics
    freq_stats = calculate_frequency_statistics(failures, total_cases)
    
    # Calculate per-intent statistics
    intent_data = {}  # Would load from actual intent results
    intent_stats = calculate_per_intent_statistics(failures, intent_data)
    
    # Identify weakest intents
    weakest_intents = identify_weakest_intents(intent_stats)
    
    # Pipeline stage analysis (Section 23)
    stages = [
        "INPUT", "PREPROCESSING", "INTENT", "RETRIEVAL",
        "EVIDENCE", "GENERATION", "GROUNDING", "ESCALATION", "SYSTEM"
    ]
    severity_weights = {"LOW": 1, "MEDIUM": 2, "HIGH": 4, "CRITICAL": 8}
    stage_analysis = {}

    for stage in stages:
        stage_failures = [
            f for f in failures
            if CATEGORY_TO_STAGE.get(f.get("primary_category", ""), "SYSTEM") == stage
        ]
        sev_counts = Counter(f.get("severity", "LOW") for f in stage_failures)
        sev_score = sum(sev_counts[s] * severity_weights[s] for s in sev_counts)
        stage_analysis[stage] = {
            "failure_count": len(stage_failures),
            "failure_rate": round(len(stage_failures) / total_cases, 4) if total_cases > 0 else 0.0,
            "severity_breakdown": dict(sev_counts),
            "severity_weighted_score": sev_score,
            "critical_count": sev_counts.get("CRITICAL", 0),
            "high_count": sev_counts.get("HIGH", 0),
            "medium_count": sev_counts.get("MEDIUM", 0),
            "low_count": sev_counts.get("LOW", 0),
        }

    highest_failure_stage = max(stages, key=lambda s: stage_analysis[s]["failure_count"])
    highest_severity_stage = max(
        stages,
        key=lambda s: (stage_analysis[s]["critical_count"], stage_analysis[s]["severity_weighted_score"]),
    )
    # Upstream bottlenecks originate in INPUT, INTENT, or RETRIEVAL
    upstream_stages = ["INPUT", "PREPROCESSING", "INTENT", "RETRIEVAL"]
    most_common_upstream_bottleneck = max(upstream_stages, key=lambda s: stage_analysis[s]["failure_count"])

    stage_output = {
        "total_cases": total_cases,
        "stages": stage_analysis,
        "highest_failure_stage": highest_failure_stage,
        "highest_severity_stage": highest_severity_stage,
        "most_common_upstream_bottleneck": most_common_upstream_bottleneck,
        "summary": {
            "highest_failure_stage_count": stage_analysis[highest_failure_stage]["failure_count"],
            "highest_severity_stage_critical_count": stage_analysis[highest_severity_stage]["critical_count"],
            "upstream_bottleneck_count": stage_analysis[most_common_upstream_bottleneck]["failure_count"],
        },
    }

    stage_output_path = "evaluation/results/failure_by_pipeline_stage.json"
    with open(stage_output_path, "w", encoding="utf-8") as f:
        json.dump(stage_output, f, indent=2)
    print(f"Pipeline stage analysis saved to: {stage_output_path}")

    # Save frequency results
    output = {
        "frequency_statistics": freq_stats,
        "intent_statistics": intent_stats,
        "weakest_intents": weakest_intents,
        "pipeline_stages": stage_output,
    }
    
    output_path = "evaluation/results/failure_frequency.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print(f"\nFrequency Statistics:")
    print(f"  Total failures: {freq_stats['total_failures']}")
    print(f"  Failure rate: {freq_stats['failure_rate']:.1%}")
    
    print(f"\nBy Category:")
    for cat, count in list(freq_stats["by_category"].items())[:5]:
        print(f"  {cat}: {count}")
    
    print(f"\nBy Severity:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = freq_stats["by_severity"].get(sev, 0)
        print(f"  {sev}: {count}")
    
    print(f"\nBy Pipeline Stage:")
    for stage, count in list(freq_stats["by_pipeline_stage"].items())[:5]:
        print(f"  {stage}: {count}")
    
    print(f"\nWeakest Intents:")
    for intent in weakest_intents[:5]:
        print(f"  {intent['intent']}: {intent['failure_count']} failures")
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
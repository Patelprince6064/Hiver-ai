"""Failure Analysis by Intent.

For every intent with sufficient data, calculate failure metrics.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


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


def analyze_intent_failures(failures: list[dict]) -> dict:
    """Analyze failures by intent category.
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Intent-level failure analysis.
    """
    # Group failures by intent
    intent_failures = defaultdict(list)
    
    for failure in failures:
        intent = failure.get("predicted_intent", "unknown")
        if not intent:
            intent = "unknown"
        intent_failures[intent].append(failure)
    
    # Analyze each intent
    intent_analysis = {}
    
    for intent, intent_fail_list in intent_failures.items():
        # Calculate metrics
        total_failures = len(intent_fail_list)
        
        # Category distribution
        category_counts = Counter(f.get("primary_category", "UNKNOWN") for f in intent_fail_list)
        
        # Severity distribution
        severity_counts = Counter(f.get("severity", "LOW") for f in intent_fail_list)
        
        # Grounding failures
        grounding_failures = sum(
            1 for f in intent_fail_list
            if f.get("primary_category") == "GROUNDING_FAILURE"
        )
        
        # Retrieval failures
        retrieval_failures = sum(
            1 for f in intent_fail_list
            if f.get("primary_category") == "RETRIEVAL_FAILURE"
        )
        
        # Escalation failures
        escalation_failures = sum(
            1 for f in intent_fail_list
            if f.get("primary_category") == "ESCALATION_FAILURE"
        )
        
        # Top failure tags
        tag_counts = Counter()
        for f in intent_fail_list:
            for tag in f.get("failure_tags", []):
                tag_counts[tag] += 1
        
        intent_analysis[intent] = {
            "failure_count": total_failures,
            "top_categories": dict(category_counts.most_common(3)),
            "top_severity": severity_counts.most_common(1)[0][0] if severity_counts else "LOW",
            "grounding_failures": grounding_failures,
            "retrieval_failures": retrieval_failures,
            "escalation_failures": escalation_failures,
            "top_failure_tags": dict(tag_counts.most_common(5)),
            "sample_failures": [
                {
                    "failure_id": f.get("failure_id", ""),
                    "secondary_category": f.get("secondary_category", ""),
                    "severity": f.get("severity", ""),
                    "root_cause": f.get("root_cause", "")[:100],
                }
                for f in intent_fail_list[:3]
            ],
        }
    
    return intent_analysis


def identify_weakest_intents(intent_analysis: dict, min_failures: int = 2) -> list[dict]:
    """Identify weakest intents by failure count.
    
    Args:
        intent_analysis: Intent-level analysis.
        min_failures: Minimum failures to consider.
        
    Returns:
        Sorted list of weakest intents.
    """
    weak_intents = []
    
    for intent, stats in intent_analysis.items():
        if stats["failure_count"] >= min_failures:
            # Calculate weakness score
            weakness_score = (
                stats["failure_count"] * 2
                + stats["grounding_failures"] * 3
                + stats["retrieval_failures"] * 2
                + stats["escalation_failures"] * 4
            )
            
            weak_intents.append({
                "intent": intent,
                "failure_count": stats["failure_count"],
                "weakness_score": weakness_score,
                "top_categories": stats["top_categories"],
                "top_severity": stats["top_severity"],
                "grounding_failures": stats["grounding_failures"],
                "retrieval_failures": stats["retrieval_failures"],
                "escalation_failures": stats["escalation_failures"],
                "sample_failures": stats["sample_failures"],
            })
    
    # Sort by weakness score (descending)
    weak_intents.sort(key=lambda x: x["weakness_score"], reverse=True)
    
    return weak_intents


def main():
    """Main entry point."""
    print("=" * 60)
    print("FAILURE ANALYSIS BY INTENT")
    print("=" * 60)
    
    # Load failure candidates
    failures_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(failures_path)
    
    print(f"\nLoaded {len(failures)} failures")
    
    # Analyze by intent
    intent_analysis = analyze_intent_failures(failures)
    
    # Identify weakest intents
    weakest_intents = identify_weakest_intents(intent_analysis)
    
    # Save results
    output = {
        "intent_analysis": intent_analysis,
        "weakest_intents": weakest_intents,
    }
    
    output_path = "evaluation/results/failure_by_intent.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print(f"\nIntent Analysis Summary:")
    print(f"  Intents analyzed: {len(intent_analysis)}")
    
    print(f"\nTop 5 Weakest Intents:")
    for i, intent in enumerate(weakest_intents[:5], 1):
        print(f"  {i}. {intent['intent']}:")
        print(f"     Failures: {intent['failure_count']}")
        print(f"     Top category: {list(intent['top_categories'].keys())[0] if intent['top_categories'] else 'N/A'}")
        print(f"     Grounding failures: {intent['grounding_failures']}")
        print(f"     Retrieval failures: {intent['retrieval_failures']}")
        print(f"     Escalation failures: {intent['escalation_failures']}")
    
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
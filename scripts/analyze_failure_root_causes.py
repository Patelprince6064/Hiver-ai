"""Analyze Failure Root Causes.

Determines the most likely root cause for each candidate failure.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import (
    PrimaryCategory,
    SecondaryCategory,
    CATEGORY_TO_STAGE,
)


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


def analyze_root_cause(failure: dict) -> dict:
    """Analyze root cause for a single failure.
    
    Args:
        failure: Failure dictionary.
        
    Returns:
        Updated failure with root cause analysis.
    """
    primary_category = failure.get("primary_category", "")
    secondary_category = failure.get("secondary_category", "")
    failure_tags = failure.get("failure_tags", [])
    
    # Default root cause
    root_cause = "Unknown"
    root_cause_confidence = "LOW"
    hypothesis = ""
    recommended_next_step = ""
    
    # Analyze based on primary category
    if primary_category == PrimaryCategory.INTENT_CLASSIFICATION_FAILURE.value:
        if secondary_category == SecondaryCategory.WRONG_INTENT.value:
            root_cause = "Intent classifier predicted wrong intent"
            root_cause_confidence = "HIGH"
            hypothesis = "Semantic similarity between intent classes caused confusion"
            recommended_next_step = "Analyze confusion matrix for intent pairs"
        elif secondary_category == SecondaryCategory.LOW_CONFIDENCE.value:
            root_cause = "Low confidence in intent prediction"
            root_cause_confidence = "HIGH"
            hypothesis = "Input lacked clear signal for intent classification"
            recommended_next_step = "Implement confidence-based routing"
        elif secondary_category == SecondaryCategory.AMBIGUOUS_INTENT.value:
            root_cause = "Ambiguous input with multiple possible intents"
            root_cause_confidence = "MEDIUM"
            hypothesis = "Customer message could reasonably map to multiple intents"
            recommended_next_step = "Consider multi-intent handling"
    
    elif primary_category == PrimaryCategory.RETRIEVAL_FAILURE.value:
        if secondary_category == SecondaryCategory.NO_RELEVANT_EVIDENCE.value:
            root_cause = "No relevant evidence found in knowledge base"
            root_cause_confidence = "HIGH"
            hypothesis = "Knowledge base lacks coverage for this query type"
            recommended_next_step = "Expand knowledge base coverage"
        elif secondary_category == SecondaryCategory.WRONG_EVIDENCE.value:
            root_cause = "Retrieved evidence does not match query intent"
            root_cause_confidence = "MEDIUM"
            hypothesis = "Semantic retrieval returned semantically similar but irrelevant evidence"
            recommended_next_step = "Improve evidence relevance filtering"
        elif secondary_category == SecondaryCategory.LOW_SIMILARITY.value:
            root_cause = "Low similarity scores for retrieved evidence"
            root_cause_confidence = "HIGH"
            hypothesis = "Query representation differs significantly from evidence representations"
            recommended_next_step = "Improve query/evidence encoding"
    
    elif primary_category == PrimaryCategory.GENERATION_FAILURE.value:
        if secondary_category == SecondaryCategory.TOO_GENERIC.value:
            root_cause = "Generated reply is too generic"
            root_cause_confidence = "MEDIUM"
            hypothesis = "LLM defaulted to generic response without using specific evidence"
            recommended_next_step = "Strengthen evidence grounding in prompts"
        elif secondary_category == SecondaryCategory.INCOMPLETE.value:
            root_cause = "Generated reply is incomplete"
            root_cause_confidence = "MEDIUM"
            hypothesis = "LLM did not address all aspects of the customer query"
            recommended_next_step = "Improve query decomposition"
        elif secondary_category == SecondaryCategory.UNHELPFUL.value:
            root_cause = "Generated reply is unhelpful"
            root_cause_confidence = "MEDIUM"
            hypothesis = "Reply did not address the customer's actual need"
            recommended_next_step = "Analyze intent-reply alignment"
        elif secondary_category == SecondaryCategory.WRONG_RESOLUTION.value:
            root_cause = "Generated reply provides wrong resolution"
            root_cause_confidence = "HIGH"
            hypothesis = "Reply contradicts evidence or policy"
            recommended_next_step = "Strengthen policy grounding"
    
    elif primary_category == PrimaryCategory.GROUNDING_FAILURE.value:
        if secondary_category == SecondaryCategory.UNSUPPORTED_CLAIM.value:
            root_cause = "Reply contains claims not supported by evidence"
            root_cause_confidence = "HIGH"
            hypothesis = "LLM generated plausible but unverified information"
            recommended_next_step = "Implement stricter grounding verification"
        elif secondary_category == SecondaryCategory.UNSUPPORTED_PRICE.value:
            root_cause = "Reply contains unsupported price information"
            root_cause_confidence = "HIGH"
            hypothesis = "LLM hallucinated price details"
            recommended_next_step = "Prohibit price claims without evidence"
        elif secondary_category == SecondaryCategory.UNSUPPORTED_TIMELINE.value:
            root_cause = "Reply contains unsupported timeline information"
            root_cause_confidence = "HIGH"
            hypothesis = "LLM hallucinated timeline details"
            recommended_next_step = "Prohibit timeline claims without evidence"
    
    elif primary_category == PrimaryCategory.ESCALATION_FAILURE.value:
        if secondary_category == SecondaryCategory.UNSAFE_AUTO_HANDLE.value:
            root_cause = "High-risk request auto-handled instead of escalated"
            root_cause_confidence = "HIGH"
            hypothesis = "Risk detection failed to identify high-risk indicators"
            recommended_next_step = "Strengthen high-risk detection rules"
        elif secondary_category == SecondaryCategory.UNNECESSARY_ESCALATION.value:
            root_cause = "Safe request unnecessarily escalated"
            root_cause_confidence = "MEDIUM"
            hypothesis = "Conservative policy triggered escalation for safe cases"
            recommended_next_step = "Review escalation thresholds"
        elif secondary_category == SecondaryCategory.MISSED_HIGH_RISK_CASE.value:
            root_cause = "High-risk case not identified"
            root_cause_confidence = "HIGH"
            hypothesis = "Risk indicators were not captured by detection rules"
            recommended_next_step = "Expand risk indicator coverage"
        elif secondary_category == SecondaryCategory.INCORRECT_ESCALATION_REASON.value:
            root_cause = "Escalation triggered due to borderline threshold or low intent confidence"
            root_cause_confidence = "HIGH"
            hypothesis = "Heuristic threshold was sensitive to mild ambiguity"
            recommended_next_step = "Calibrate escalation thresholds per intent on validation data"
    
    elif primary_category == PrimaryCategory.EVALUATION_FAILURE.value:
        if secondary_category == SecondaryCategory.JUDGE_DISAGREEMENT.value:
            root_cause = "Human and LLM judges disagree on quality"
            root_cause_confidence = "LOW"
            hypothesis = "Rubric ambiguity or judge bias may be present"
            recommended_next_step = "Analyze disagreement patterns"
    
    # Update failure record
    failure["root_cause"] = root_cause
    failure["root_cause_confidence"] = root_cause_confidence
    failure["hypothesis"] = hypothesis
    failure["recommended_next_step"] = recommended_next_step
    
    return failure


def analyze_root_causes(failures: list[dict]) -> list[dict]:
    """Analyze root causes for all failures.
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Updated failures with root cause analysis.
    """
    updated_failures = []
    
    for failure in failures:
        updated = analyze_root_cause(failure)
        updated_failures.append(updated)
    
    return updated_failures


def save_failures(failures: list[dict], output_path: str) -> None:
    """Save failures to JSONL file."""
    with open(output_path, "w") as f:
        for failure in failures:
            f.write(json.dumps(failure) + "\n")


def main():
    """Main entry point."""
    print("=" * 60)
    print("ANALYZING FAILURE ROOT CAUSES")
    print("=" * 60)
    
    # Load failure candidates
    input_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(input_path)
    
    print(f"\nLoaded {len(failures)} failure candidates")
    
    # Analyze root causes
    updated_failures = analyze_root_causes(failures)
    
    # Save updated failures
    output_path = "evaluation/results/failure_candidates.jsonl"
    save_failures(updated_failures, output_path)
    
    # Print summary
    print(f"\nRoot Cause Analysis Summary:")
    
    # Count by root cause
    root_cause_counts = {}
    for failure in updated_failures:
        rc = failure.get("root_cause", "Unknown")
        root_cause_counts[rc] = root_cause_counts.get(rc, 0) + 1
    
    print("\nTop Root Causes:")
    for rc, count in sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {rc}: {count}")
    
    # Count by confidence
    confidence_counts = {}
    for failure in updated_failures:
        conf = failure.get("root_cause_confidence", "LOW")
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    print("\nConfidence Levels:")
    for conf in ["HIGH", "MEDIUM", "LOW"]:
        count = confidence_counts.get(conf, 0)
        print(f"  {conf}: {count}")
    
    print(f"\nUpdated failures saved to: {output_path}")


if __name__ == "__main__":
    main()
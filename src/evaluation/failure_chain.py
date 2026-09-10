"""Failure Chain Representation.

Represents failures as chains through pipeline stages.
"""

from dataclasses import dataclass, field
from typing import Optional

from src.evaluation.failure_analysis_schema import PIPELINE_STAGES, CATEGORY_TO_STAGE


@dataclass
class FailureChain:
    """Represents a failure chain through the pipeline."""
    failure_id: str
    chain: list[str] = field(default_factory=list)
    root_stage: str = ""
    final_stage: str = ""
    propagation_depth: int = 0
    
    def add_stage(self, stage: str) -> None:
        """Add a stage to the chain."""
        if stage not in self.chain:
            self.chain.append(stage)
            self.propagation_depth = len(self.chain) - 1
    
    def get_root_cause(self) -> str:
        """Get the root cause stage (first in chain)."""
        return self.chain[0] if self.chain else ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "failure_id": self.failure_id,
            "chain": self.chain,
            "root_stage": self.root_stage,
            "final_stage": self.final_stage,
            "propagation_depth": self.propagation_depth,
        }


def build_failure_chain(
    failure_id: str,
    primary_categories: list[str],
) -> FailureChain:
    """Build a failure chain from primary categories.
    
    Args:
        failure_id: Unique failure identifier.
        list of primary categories observed.
        
    Returns:
        FailureChain object.
    """
    chain = FailureChain(failure_id=failure_id)
    
    for category in primary_categories:
        stage = CATEGORY_TO_STAGE.get(category, "SYSTEM")
        chain.add_stage(stage)
    
    if chain.chain:
        chain.root_stage = chain.chain[0]
        chain.final_stage = chain.chain[-1]
    
    return chain


def analyze_propagation(
    failures: list[dict],
) -> dict:
    """Analyze failure propagation patterns.
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Propagation analysis results.
    """
    propagation_counts = {}
    stage_transitions = {}
    
    for failure in failures:
        categories = failure.get("failure_chain", [])
        if not categories:
            continue
        
        # Count propagation depth
        depth = len(set(categories))
        propagation_counts[depth] = propagation_counts.get(depth, 0) + 1
        
        # Count stage transitions
        for i in range(len(categories) - 1):
            from_stage = CATEGORY_TO_STAGE.get(categories[i], "SYSTEM")
            to_stage = CATEGORY_TO_STAGE.get(categories[i + 1], "SYSTEM")
            transition = f"{from_stage} -> {to_stage}"
            stage_transitions[transition] = stage_transitions.get(transition, 0) + 1
    
    # Sort transitions by count
    sorted_transitions = sorted(
        stage_transitions.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    
    return {
        "propagation_depths": propagation_counts,
        "common_transitions": sorted_transitions[:10],
        "total_failures_with_chain": sum(propagation_counts.values()),
    }


def calculate_conditional_probabilities(
    failures: list[dict],
) -> dict:
    """Calculate conditional probabilities of failure propagation.
    
    P(reply failure | intent failure)
    P(reply failure | retrieval failure)
    P(reply failure | grounding failure)
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Conditional probabilities.
    """
    # Count occurrences
    stage_counts = {}
    pair_counts = {}
    
    for failure in failures:
        categories = set(failure.get("failure_chain", []))
        
        for category in categories:
            stage = CATEGORY_TO_STAGE.get(category, "SYSTEM")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        # Count pairs
        category_list = list(categories)
        for i in range(len(category_list)):
            for j in range(len(category_list)):
                if i != j:
                    stage_i = CATEGORY_TO_STAGE.get(category_list[i], "SYSTEM")
                    stage_j = CATEGORY_TO_STAGE.get(category_list[j], "SYSTEM")
                    pair = (stage_i, stage_j)
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1
    
    # Calculate conditional probabilities
    conditional_probs = {}
    
    # P(reply failure | intent failure)
    intent_count = stage_counts.get("INTENT", 0)
    intent_and_reply = pair_counts.get(("INTENT", "GENERATION"), 0)
    if intent_count > 0:
        conditional_probs["P(GENERATION | INTENT)"] = intent_and_reply / intent_count
    
    # P(reply failure | retrieval failure)
    retrieval_count = stage_counts.get("RETRIEVAL", 0)
    retrieval_and_reply = pair_counts.get(("RETRIEVAL", "GENERATION"), 0)
    if retrieval_count > 0:
        conditional_probs["P(GENERATION | RETRIEVAL)"] = retrieval_and_reply / retrieval_count
    
    # P(reply failure | grounding failure)
    grounding_count = stage_counts.get("GROUNDING", 0)
    grounding_and_reply = pair_counts.get(("GROUNDING", "GENERATION"), 0)
    if grounding_count > 0:
        conditional_probs["P(GENERATION | GROUNDING)"] = grounding_and_reply / grounding_count
    
    return {
        "stage_counts": stage_counts,
        "conditional_probabilities": conditional_probs,
        "note": "These are observational associations, not causal claims.",
    }
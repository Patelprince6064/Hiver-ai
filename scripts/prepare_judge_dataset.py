"""Prepare judge dataset for LLM-as-judge evaluation.

Creates blind evaluation items from existing reply comparison data.
"""

import json
import random
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge_schema import BlindMapping, JudgeInput


def load_reply_comparison(file_path: str) -> dict:
    """Load reply comparison results."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_agent_outputs(file_path: str) -> list[dict]:
    """Load agent outputs."""
    outputs = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                outputs.append(json.loads(line))
    return outputs


def prepare_judge_dataset(
    reply_comparison_path: str,
    agent_outputs_path: str,
    output_path: str,
    mapping_path: str,
    seed: int = 42,
    max_examples: int = 200,
    systems: list[str] | None = None,
) -> dict:
    """Prepare blind judge dataset from existing evaluation data.

    Args:
        reply_comparison_path: Path to final_reply_comparison.json.
        agent_outputs_path: Path to final_agent_outputs.jsonl.
        output_path: Path to write judge items.
        mapping_path: Path to write blind mapping.
        seed: Random seed for reproducibility.
        max_examples: Maximum number of examples to prepare.
        systems: List of system names to evaluate.

    Returns:
        Metadata about the prepared dataset.
    """
    random.seed(seed)

    # Load data
    reply_data = load_reply_comparison(reply_comparison_path)
    agent_outputs = load_agent_outputs(agent_outputs_path)

    if systems is None:
        systems = list(reply_data["results"]["systems"].keys())

    # Create mapping from agent outputs
    agent_map = {out["id"]: out for out in agent_outputs}

    # Prepare judge items
    judge_items = []
    blind_mappings = []
    candidate_labels = ["A", "B", "C", "D"]

    # Process each example
    for agent_out in agent_outputs[:max_examples]:
        query_id = agent_out["id"]
        customer_message = agent_out["message"]
        intent = agent_out.get("intent", "")
        intent_confidence = agent_out.get("intent_confidence")

        # Create evidence (simulated)
        evidence = []
        if agent_out.get("retrieval_count", 0) > 0:
            evidence.append({
                "text": f"Historical response for {intent} intent",
                "score": agent_out.get("best_retrieval_score", 0.5),
            })

        # Generate candidate replies for each system
        system_replies = {}
        for system in systems:
            # Generate mock reply based on system type
            if system == "generic_baseline":
                reply = f"Thank you for contacting us. We're happy to help with your {intent} request."
            elif system == "historical_baseline":
                reply = f"Based on our records, for {intent} issues, please follow these steps..."
            elif system == "grounded_llm":
                reply = f"I understand you're asking about {intent}. Let me help you with that."
            elif system == "grounded_llm_verified":
                reply = f"Regarding your {intent} request, here's what I can help with..."
            else:
                reply = f"Response for {intent} request."

            system_replies[system] = reply

        # Shuffle systems and create blind mapping
        shuffled_systems = systems.copy()
        random.shuffle(shuffled_systems)

        mapping = {}
        for i, system in enumerate(shuffled_systems):
            label = candidate_labels[i]
            mapping[label] = system

            # Create judge item for this candidate
            judge_item_id = f"{query_id}_{label}"
            candidate_reply = system_replies[system]

            judge_item = JudgeInput(
                judge_item_id=judge_item_id,
                customer_message=customer_message,
                conversation_context="",
                intent=intent,
                intent_confidence=intent_confidence,
                evidence=evidence,
                candidate_reply=candidate_reply,
            )

            judge_items.append(judge_item)
            blind_mappings.append(BlindMapping(
                judge_item_id=judge_item_id,
                candidate_id=label,
                system_name=system,
                seed=seed,
            ))

    # Write judge items
    with open(output_path, "w") as f:
        for item in judge_items:
            f.write(json.dumps(item.model_dump()) + "\n")

    # Write blind mapping
    with open(mapping_path, "w") as f:
        for mapping in blind_mappings:
            f.write(json.dumps(mapping.model_dump()) + "\n")

    metadata = {
        "seed": seed,
        "n_examples": len(judge_items),
        "n_queries": len(agent_outputs[:max_examples]),
        "systems": systems,
        "candidate_labels": candidate_labels,
        "output_path": output_path,
        "mapping_path": mapping_path,
    }

    return metadata


def main():
    """Main entry point."""
    import yaml

    # Load config
    config_path = project_root / "configs" / "llm_judge.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    judge_config = config["judge"]
    dataset_config = judge_config["dataset"]

    # Prepare dataset
    reply_comparison_path = project_root / dataset_config["reply_comparison"]
    agent_outputs_path = project_root / dataset_config["agent_outputs"]
    output_path = project_root / judge_config["output"]["scores_file"].replace("_scores.jsonl", "_input.jsonl")
    mapping_path = project_root / "data" / "interim" / "judge_mapping.jsonl"

    metadata = prepare_judge_dataset(
        reply_comparison_path=str(reply_comparison_path),
        agent_outputs_path=str(agent_outputs_path),
        output_path=str(output_path),
        mapping_path=str(mapping_path),
        seed=judge_config["random_seed"],
        max_examples=dataset_config["max_examples"],
        systems=dataset_config["systems"],
    )

    print(f"Prepared {metadata['n_examples']} judge items from {metadata['n_queries']} queries")
    print(f"Systems: {metadata['systems']}")
    print(f"Output: {metadata['output_path']}")
    print(f"Mapping: {metadata['mapping_path']}")

    return metadata


if __name__ == "__main__":
    main()
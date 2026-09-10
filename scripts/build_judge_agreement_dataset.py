"""Build judge agreement dataset.

Creates a matched dataset containing examples where both human and LLM judge scores exist.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_jsonl(file_path: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def build_agreement_dataset(
    human_scores_file: str,
    llm_scores_file: str,
    llm_input_file: str,
    agent_outputs_file: str,
    output_file: str,
) -> dict:
    """Build matched agreement dataset.

    Args:
        human_scores_file: Path to human-LLM comparison file.
        llm_scores_file: Path to LLM judge scores file.
        llm_input_file: Path to LLM judge input file.
        agent_outputs_file: Path to agent outputs file.
        output_file: Path to write matched dataset.

    Returns:
        Dataset statistics.
    """
    # Load data
    human_data = load_jsonl(human_scores_file)
    llm_scores = load_jsonl(llm_scores_file)
    llm_inputs = load_jsonl(llm_input_file)
    agent_outputs = load_jsonl(agent_outputs_file)

    # Create lookup dictionaries
    llm_score_map = {item["judge_item_id"]: item for item in llm_scores}
    llm_input_map = {item["judge_item_id"]: item for item in llm_inputs}
    agent_output_map = {item["id"]: item for item in agent_outputs}

    # Build matched dataset
    matched_dataset = []
    seen_ids = set()

    for human_item in human_data:
        judge_item_id = human_item["judge_item_id"]

        # Skip duplicates
        if judge_item_id in seen_ids:
            continue
        seen_ids.add(judge_item_id)

        # Find matching LLM score
        if judge_item_id not in llm_score_map:
            continue

        llm_score = llm_score_map[judge_item_id]
        llm_input = llm_input_map.get(judge_item_id, {})

        # Extract query ID and system from judge_item_id
        # Format: eval_XXXX_Y where XXXX is query number and Y is system label
        parts = judge_item_id.split("_")
        if len(parts) >= 3:
            query_num = parts[1]
            system_label = parts[2]
            query_id = f"eval_{query_num}"
        else:
            query_id = judge_item_id
            system_label = "unknown"

        # Get agent output for additional context
        agent_output = agent_output_map.get(query_id, {})

        # Create matched record
        matched_record = {
            "query_id": query_id,
            "judge_item_id": judge_item_id,
            "system_label": system_label,
            "customer_message": llm_input.get("customer_message", ""),
            "intent": llm_input.get("intent", ""),
            "candidate_reply": llm_input.get("candidate_reply", ""),
            "human_scores": {
                "relevance": human_item.get("human_relevance", 3),
                "groundedness": human_item.get("human_groundedness", 3),
                "correctness": human_item.get("human_correctness", 3),
                "helpfulness": human_item.get("human_helpfulness", 3),
                "completeness": human_item.get("human_completeness", 3),
                "style": human_item.get("human_style", 3),
                "overall": human_item.get("human_overall", 3.0),
            },
            "llm_scores": {
                "relevance": llm_score.get("relevance", 3),
                "groundedness": llm_score.get("groundedness", 3),
                "correctness": llm_score.get("correctness", 3),
                "helpfulness": llm_score.get("helpfulness", 3),
                "completeness": llm_score.get("completeness", 3),
                "style": llm_score.get("style", 3),
                "overall": llm_score.get("overall", 3.0),
            },
            "human_failure_tags": agent_output.get("escalation_reasons", []),
            "llm_failure_tags": llm_score.get("failure_tags", []),
            "llm_rationale": llm_score.get("short_rationale", ""),
            "difficulty": agent_output.get("difficulty", "unknown"),
            "ambiguity": agent_output.get("ambiguity", "unknown"),
        }

        matched_dataset.append(matched_record)

    # Write matched dataset
    with open(output_file, "w") as f:
        for record in matched_dataset:
            f.write(json.dumps(record) + "\n")

    # Calculate statistics
    stats = {
        "total_human_records": len(human_data),
        "total_llm_records": len(llm_scores),
        "matched_records": len(matched_dataset),
        "unique_queries": len(set(r["query_id"] for r in matched_dataset)),
        "systems": list(set(r["system_label"] for r in matched_dataset)),
        "output_file": output_file,
    }

    return stats


def main():
    """Main entry point."""
    print("=" * 60)
    print("BUILDING JUDGE AGREEMENT DATASET")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]

    # Build dataset
    stats = build_agreement_dataset(
        human_scores_file=str(project_root / dataset_config["human_scores_file"]),
        llm_scores_file=str(project_root / dataset_config["llm_scores_file"]),
        llm_input_file=str(project_root / dataset_config["llm_input_file"]),
        agent_outputs_file=str(project_root / dataset_config["agent_outputs_file"]),
        output_file=str(project_root / dataset_config["output_file"]),
    )

    print(f"\nDataset Statistics:")
    print(f"  Human records: {stats['total_human_records']}")
    print(f"  LLM records: {stats['total_llm_records']}")
    print(f"  Matched records: {stats['matched_records']}")
    print(f"  Unique queries: {stats['unique_queries']}")
    print(f"  Systems: {stats['systems']}")
    print(f"  Output: {stats['output_file']}")

    return stats


if __name__ == "__main__":
    main()
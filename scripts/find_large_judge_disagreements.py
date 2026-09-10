"""Find large judge disagreements.

Identifies cases where human and LLM scores differ significantly.
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


def find_large_disagreements(
    dataset: list[dict],
    output_file: str,
    threshold: float = 2.0,
) -> dict:
    """Find cases with large disagreements.

    Args:
        dataset: Matched evaluation dataset.
        output_file: Path to write disagreement cases.
        threshold: Minimum absolute difference to consider.

    Returns:
        Large disagreement analysis.
    """
    large_disagreements = []
    human_high_llm_low = []
    human_low_llm_high = []

    for record in dataset:
        human_overall = record.get("human_scores", {}).get("overall", 3.0)
        llm_overall = record.get("llm_scores", {}).get("overall", 3.0)
        difference = llm_overall - human_overall

        if abs(difference) >= threshold:
            disagreement_record = {
                "query_id": record.get("query_id", ""),
                "judge_item_id": record.get("judge_item_id", ""),
                "system_label": record.get("system_label", ""),
                "customer_message": record.get("customer_message", ""),
                "candidate_reply": record.get("candidate_reply", ""),
                "human_scores": record.get("human_scores", {}),
                "llm_scores": record.get("llm_scores", {}),
                "difference": round(difference, 4),
                "abs_difference": round(abs(difference), 4),
                "human_failure_tags": record.get("human_failure_tags", []),
                "llm_failure_tags": record.get("llm_failure_tags", []),
                "llm_rationale": record.get("llm_rationale", ""),
                "difficulty": record.get("difficulty", "unknown"),
            }
            large_disagreements.append(disagreement_record)

            # Categorize
            if human_overall >= 4 and llm_overall <= 2:
                human_high_llm_low.append(disagreement_record)
            elif human_overall <= 2 and llm_overall >= 4:
                human_low_llm_high.append(disagreement_record)

    # Sort by disagreement magnitude
    large_disagreements.sort(key=lambda x: x["abs_difference"], reverse=True)
    human_high_llm_low.sort(key=lambda x: x["abs_difference"], reverse=True)
    human_low_llm_high.sort(key=lambda x: x["abs_difference"], reverse=True)

    # Write results
    with open(output_file, "w") as f:
        for record in large_disagreements:
            f.write(json.dumps(record) + "\n")

    results = {
        "total_large_disagreements": len(large_disagreements),
        "human_high_llm_low_count": len(human_high_llm_low),
        "human_low_llm_high_count": len(human_low_llm_high),
        "threshold": threshold,
        "output_file": output_file,
        "top_disagreements": large_disagreements[:5],
        "human_high_llm_low_examples": human_high_llm_low[:3],
        "human_low_llm_high_examples": human_low_llm_high[:3],
    }

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("FINDING LARGE JUDGE DISAGREEMENTS")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_file = str(project_root / "evaluation" / "results" / "large_judge_disagreements.jsonl")

    # Load dataset
    dataset = load_jsonl(dataset_file)
    print(f"Loaded {len(dataset)} matched records")

    # Find disagreements
    results = find_large_disagreements(dataset, output_file, threshold=2.0)

    # Print summary
    print("\n" + "=" * 60)
    print("LARGE DISAGREEMENT SUMMARY")
    print("=" * 60)

    print(f"\nTotal large disagreements (>= 2.0): {results['total_large_disagreements']}")
    print(f"Human high / LLM low: {results['human_high_llm_low_count']}")
    print(f"Human low / LLM high: {results['human_low_llm_high_count']}")

    if results["top_disagreements"]:
        print("\nTop 5 Disagreements:")
        for i, dis in enumerate(results["top_disagreements"], 1):
            print(f"  {i}. Query: {dis['query_id']}, System: {dis['system_label']}")
            print(f"     Human: {dis['human_scores']['overall']:.2f}, LLM: {dis['llm_scores']['overall']:.2f}, Diff: {dis['difference']:.2f}")

    if results["human_high_llm_low_examples"]:
        print("\nHuman High / LLM Low Examples:")
        for ex in results["human_high_llm_low_examples"][:2]:
            print(f"  - {ex['query_id']}: Human={ex['human_scores']['overall']:.2f}, LLM={ex['llm_scores']['overall']:.2f}")

    if results["human_low_llm_high_examples"]:
        print("\nHuman Low / LLM High Examples:")
        for ex in results["human_low_llm_high_examples"][:2]:
            print(f"  - {ex['query_id']}: Human={ex['human_scores']['overall']:.2f}, LLM={ex['llm_scores']['overall']:.2f}")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
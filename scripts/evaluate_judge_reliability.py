"""Evaluate judge reliability.

Measures judge consistency by running repeated evaluations.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge import MockJudge
from src.evaluation.judge_schema import JudgeInput, JudgeResult


def load_judge_items(file_path: str) -> list[JudgeInput]:
    """Load judge items from file."""
    items = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                items.append(JudgeInput(**data))
    return items


def evaluate_reliability(judge, items: list[JudgeInput], repeat_count: int = 3) -> dict:
    """Evaluate judge reliability by running repeated evaluations.

    Args:
        judge: Judge instance.
        items: List of judge items.
        repeat_count: Number of times to repeat each evaluation.

    Returns:
        Reliability metrics.
    """
    print(f"Running {repeat_count} repeated evaluations on {len(items)} items...")

    # Run repeated evaluations
    all_results = []
    for repeat_idx in range(repeat_count):
        print(f"  Repeat {repeat_idx + 1}/{repeat_count}...")
        repeat_results = []
        for item in items:
            result = judge.evaluate(item)
            repeat_results.append(result)
        all_results.append(repeat_results)

    # Calculate reliability metrics
    n_items = len(items)
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
    
    # Track variance per dimension
    dimension_variance = {dim: [] for dim in dimensions}
    overall_variance = []
    score_agreements = []

    for item_idx in range(n_items):
        # Get results for this item across repeats
        item_results = [all_results[repeat_idx][item_idx] for repeat_idx in range(repeat_count)]
        
        # Calculate variance per dimension
        for dim in dimensions:
            scores = [getattr(result, dim) for result in item_results]
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            dimension_variance[dim].append(variance)
        
        # Calculate overall variance
        overall_scores = [result.overall for result in item_results]
        mean_overall = sum(overall_scores) / len(overall_scores)
        overall_var = sum((s - mean_overall) ** 2 for s in overall_scores) / len(overall_scores)
        overall_variance.append(overall_var)
        
        # Calculate score agreement (exact match)
        exact_matches = sum(
            1 for i in range(repeat_count) 
            for j in range(i + 1, repeat_count)
            if item_results[i].overall == item_results[j].overall
        )
        total_pairs = repeat_count * (repeat_count - 1) / 2
        score_agreements.append(exact_matches / total_pairs if total_pairs > 0 else 0)

    # Aggregate metrics
    reliability_result = {
        "n_examples": n_items,
        "n_repeated": n_items,
        "repeat_count": repeat_count,
        "score_agreement": round(sum(score_agreements) / len(score_agreements), 3),
        "dimension_variance": {
            dim: round(sum(var_list) / len(var_list), 4)
            for dim, var_list in dimension_variance.items()
        },
        "overall_variance": round(sum(overall_variance) / len(overall_variance), 4),
        "notes": "Variance calculated across repeated evaluations. Lower variance indicates higher reliability.",
    }

    return reliability_result


def main():
    """Main entry point."""
    import yaml

    print("=" * 60)
    print("JUDGE RELIABILITY EVALUATION")
    print("=" * 60)

    # Load config
    config_path = project_root / "configs" / "llm_judge.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    judge_config = config["judge"]

    # Load judge items
    judge_input_path = project_root / judge_config["output"]["scores_file"].replace("_scores.jsonl", "_input.jsonl")
    if not judge_input_path.exists():
        print(f"Judge input not found: {judge_input_path}")
        print("Please run prepare_judge_dataset.py and run_llm_judge.py first.")
        return

    items = load_judge_items(str(judge_input_path))
    print(f"Loaded {len(items)} items")

    # Use a subset for reliability testing (10% or max 20)
    subset_size = min(20, max(1, len(items) // 10))
    subset_items = items[:subset_size]
    print(f"Using subset of {subset_size} items for reliability testing")

    # Create judge
    judge = MockJudge(seed=judge_config["random_seed"])

    # Evaluate reliability
    reliability_result = evaluate_reliability(
        judge,
        subset_items,
        repeat_count=judge_config["reliability"]["repeat_count"],
    )

    # Save results
    output_path = project_root / "evaluation" / "results" / "judge_reliability.json"
    with open(output_path, "w") as f:
        json.dump(reliability_result, f, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("RELIABILITY SUMMARY")
    print("=" * 60)
    print(f"Examples tested: {reliability_result['n_examples']}")
    print(f"Repeat count: {reliability_result['repeat_count']}")
    print(f"Score agreement: {reliability_result['score_agreement']:.1%}")
    print(f"Overall variance: {reliability_result['overall_variance']:.4f}")
    print("\nDimension variance:")
    for dim, var in reliability_result["dimension_variance"].items():
        print(f"  {dim}: {var:.4f}")

    return reliability_result


if __name__ == "__main__":
    main()
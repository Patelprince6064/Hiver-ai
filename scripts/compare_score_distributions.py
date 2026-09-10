"""Compare score distributions between human and LLM judge.

Analyzes systematic differences in scoring patterns.
"""

import json
import math
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


def calculate_distribution_stats(scores: list[float]) -> dict:
    """Calculate distribution statistics."""
    if not scores:
        return {
            "n": 0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "frequencies": {},
        }

    n = len(scores)
    mean = sum(scores) / n
    sorted_scores = sorted(scores)
    median = sorted_scores[n // 2] if n % 2 == 1 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
    std = math.sqrt(sum((s - mean) ** 2 for s in scores) / n)
    min_score = min(scores)
    max_score = max(scores)

    # Calculate frequencies for 1-5 scale
    frequencies = {}
    for i in range(1, 6):
        frequencies[str(i)] = sum(1 for s in scores if int(round(s)) == i)

    return {
        "n": n,
        "mean": round(mean, 4),
        "median": round(median, 4),
        "std": round(std, 4),
        "min": round(min_score, 4),
        "max": round(max_score, 4),
        "frequencies": frequencies,
    }


def compare_distributions(dataset: list[dict], output_file: str) -> dict:
    """Compare human vs LLM score distributions.

    Args:
        dataset: Matched evaluation dataset.
        output_file: Path to write distribution comparison.

    Returns:
        Distribution comparison results.
    """
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style", "overall"]

    results = {
        "dimensions": {},
        "summary": {
            "systematic_differences": [],
            "potential_biases": [],
        },
    }

    for dim in dimensions:
        human_scores = []
        llm_scores = []

        for record in dataset:
            if dim == "overall":
                human_score = record.get("human_scores", {}).get("overall")
                llm_score = record.get("llm_scores", {}).get("overall")
            else:
                human_score = record.get("human_scores", {}).get(dim)
                llm_score = record.get("llm_scores", {}).get(dim)

            if human_score is not None and llm_score is not None:
                human_scores.append(float(human_score))
                llm_scores.append(float(llm_score))

        human_stats = calculate_distribution_stats(human_scores)
        llm_stats = calculate_distribution_stats(llm_scores)

        # Calculate mean difference
        mean_diff = llm_stats["mean"] - human_stats["mean"]

        results["dimensions"][dim] = {
            "human": human_stats,
            "llm": llm_stats,
            "mean_difference": round(mean_diff, 4),
            "abs_mean_difference": round(abs(mean_diff), 4),
        }

        # Check for systematic differences
        if abs(mean_diff) > 0.5:
            direction = "over-scores" if mean_diff > 0 else "under-scores"
            results["summary"]["systematic_differences"].append({
                "dimension": dim,
                "direction": direction,
                "magnitude": round(abs(mean_diff), 4),
            })

    # Check for potential verbosity bias
    human_means = [results["dimensions"][dim]["human"]["mean"] for dim in dimensions]
    llm_means = [results["dimensions"][dim]["llm"]["mean"] for dim in dimensions]

    overall_human_mean = sum(human_means) / len(human_means)
    overall_llm_mean = sum(llm_means) / len(llm_means)

    if overall_llm_mean > overall_human_mean + 0.3:
        results["summary"]["potential_biases"].append({
            "type": "over_scoring",
            "description": "LLM judge tends to score higher than human",
            "magnitude": round(overall_llm_mean - overall_human_mean, 4),
        })
    elif overall_llm_mean < overall_human_mean - 0.3:
        results["summary"]["potential_biases"].append({
            "type": "under_scoring",
            "description": "LLM judge tends to score lower than human",
            "magnitude": round(overall_human_mean - overall_llm_mean, 4),
        })

    # Write results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("COMPARING SCORE DISTRIBUTIONS")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_file = str(project_root / "evaluation" / "results" / "human_llm_score_distributions.json")

    # Load dataset
    dataset = load_jsonl(dataset_file)
    print(f"Loaded {len(dataset)} matched records")

    # Compare distributions
    results = compare_distributions(dataset, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("DISTRIBUTION COMPARISON SUMMARY")
    print("=" * 60)

    for dim, stats in results["dimensions"].items():
        print(f"\n{dim.upper()}:")
        print(f"  Human: mean={stats['human']['mean']:.3f}, std={stats['human']['std']:.3f}")
        print(f"  LLM:   mean={stats['llm']['mean']:.3f}, std={stats['llm']['std']:.3f}")
        print(f"  Difference: {stats['mean_difference']:.3f}")

    if results["summary"]["systematic_differences"]:
        print("\nSystematic Differences:")
        for diff in results["summary"]["systematic_differences"]:
            print(f"  {diff['dimension']}: LLM {diff['direction']} by {diff['magnitude']:.3f}")

    if results["summary"]["potential_biases"]:
        print("\nPotential Biases:")
        for bias in results["summary"]["potential_biases"]:
            print(f"  {bias['type']}: {bias['description']}")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
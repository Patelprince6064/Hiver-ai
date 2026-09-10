"""Analyze dimension-level agreement.

Ranks dimensions by agreement and identifies strongest/weakest dimensions.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge_agreement_metrics import calculate_dimension_agreement


def load_jsonl(file_path: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def analyze_dimension_agreement(dataset: list[dict], output_file: str) -> dict:
    """Analyze agreement by dimension.

    Args:
        dataset: Matched evaluation dataset.
        output_file: Path to write analysis results.

    Returns:
        Dimension agreement analysis.
    """
    # Calculate dimension agreement
    dimension_agreement = calculate_dimension_agreement(dataset)

    # Rank dimensions by agreement (using Spearman as primary)
    dimensions = list(dimension_agreement.keys())
    ranked_dimensions = sorted(
        dimensions,
        key=lambda d: dimension_agreement[d]["spearman"],
        reverse=True,
    )

    # Identify strongest and weakest
    strongest = ranked_dimensions[0] if ranked_dimensions else None
    weakest = ranked_dimensions[-1] if ranked_dimensions else None

    results = {
        "dimension_agreement": dimension_agreement,
        "ranking_by_spearman": ranked_dimensions,
        "strongest_dimension": strongest,
        "weakest_dimension": weakest,
        "summary": {
            "strongest_spearman": dimension_agreement[strongest]["spearman"] if strongest else 0,
            "weakest_spearman": dimension_agreement[weakest]["spearman"] if weakest else 0,
            "strongest_mae": dimension_agreement[strongest]["mae"] if strongest else 0,
            "weakest_mae": dimension_agreement[weakest]["mae"] if weakest else 0,
        },
    }

    # Write results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("ANALYZING DIMENSION-LEVEL AGREEMENT")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_file = str(project_root / "evaluation" / "results" / "dimension_agreement.json")

    # Load dataset
    dataset = load_jsonl(dataset_file)
    print(f"Loaded {len(dataset)} matched records")

    # Analyze
    results = analyze_dimension_agreement(dataset, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("DIMENSION AGREEMENT RANKING")
    print("=" * 60)

    print("\nRanking by Spearman correlation:")
    for i, dim in enumerate(results["ranking_by_spearman"], 1):
        metrics = results["dimension_agreement"][dim]
        print(f"  {i}. {dim}: Spearman={metrics['spearman']:.4f}, MAE={metrics['mae']:.4f}, Within-1={metrics['within_1_agreement']:.2%}")

    print(f"\nStrongest dimension: {results['strongest_dimension']} (Spearman={results['summary']['strongest_spearman']:.4f})")
    print(f"Weakest dimension: {results['weakest_dimension']} (Spearman={results['summary']['weakest_spearman']:.4f})")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
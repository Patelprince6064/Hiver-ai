"""Analyze judge disagreements.

Finds examples where human and LLM scores differ significantly.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_comparison_data(file_path: str) -> list[dict]:
    """Load comparison data."""
    data = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def find_disagreements(
    comparison_data: list[dict],
    threshold: float = 1.5,
) -> dict:
    """Find examples with significant disagreements.

    Args:
        comparison_data: Comparison data.
        threshold: Minimum difference to consider as disagreement.

    Returns:
        Disagreement analysis.
    """
    high_llm_low_human = []
    high_human_low_llm = []

    for record in comparison_data:
        difference = record["difference"]
        item_id = record["judge_item_id"]
        
        if difference >= threshold:
            # LLM scored higher than human
            high_llm_low_human.append({
                "judge_item_id": item_id,
                "human_score": record["human_overall"],
                "llm_score": record["llm_overall"],
                "difference": difference,
                "dimensions": {
                    dim: {
                        "human": record[f"human_{dim}"],
                        "llm": record[f"llm_{dim}"],
                    }
                    for dim in ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
                },
            })
        elif difference <= -threshold:
            # Human scored higher than LLM
            high_human_low_llm.append({
                "judge_item_id": item_id,
                "human_score": record["human_overall"],
                "llm_score": record["llm_overall"],
                "difference": difference,
                "dimensions": {
                    dim: {
                        "human": record[f"human_{dim}"],
                        "llm": record[f"llm_{dim}"],
                    }
                    for dim in ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
                },
            })

    # Sort by absolute difference
    high_llm_low_human.sort(key=lambda x: x["difference"], reverse=True)
    high_human_low_llm.sort(key=lambda x: x["difference"])

    return {
        "threshold": threshold,
        "high_llm_low_human": {
            "count": len(high_llm_low_human),
            "examples": high_llm_low_human[:10],  # Top 10
        },
        "high_human_low_llm": {
            "count": len(high_human_low_llm),
            "examples": high_human_low_llm[:10],  # Top 10
        },
        "total_disagreements": len(high_llm_low_human) + len(high_human_low_llm),
    }


def analyze_dimension_disagreements(comparison_data: list[dict]) -> dict:
    """Analyze disagreements at dimension level."""
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
    
    dimension_stats = {}
    for dim in dimensions:
        differences = [rec[f"llm_{dim}"] - rec[f"human_{dim}"] for rec in comparison_data]
        abs_differences = [abs(d) for d in differences]
        
        dimension_stats[dim] = {
            "mean_difference": round(sum(differences) / len(differences), 3) if differences else 0,
            "mean_absolute_difference": round(sum(abs_differences) / len(abs_differences), 3) if abs_differences else 0,
            "max_difference": round(max(differences), 3) if differences else 0,
            "min_difference": round(min(differences), 3) if differences else 0,
        }
    
    return dimension_stats


def main():
    """Main entry point."""
    print("=" * 60)
    print("JUDGE DISAGREEMENT ANALYSIS")
    print("=" * 60)

    # Load comparison data
    comparison_path = project_root / "evaluation" / "results" / "human_llm_comparison.jsonl"
    if not comparison_path.exists():
        print(f"Comparison data not found: {comparison_path}")
        print("Please run compare_human_llm_scores.py first.")
        return

    comparison_data = load_comparison_data(str(comparison_path))
    print(f"Loaded {len(comparison_data)} comparison records")

    # Find disagreements
    disagreements = find_disagreements(comparison_data, threshold=1.5)

    # Analyze dimension disagreements
    dimension_disagreements = analyze_dimension_disagreements(comparison_data)

    # Combine results
    analysis = {
        "n_examples": len(comparison_data),
        "disagreements": disagreements,
        "dimension_analysis": dimension_disagreements,
    }

    # Save results
    output_path = project_root / "evaluation" / "results" / "judge_disagreements.json"
    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("DISAGREEMENT SUMMARY")
    print("=" * 60)
    print(f"Total examples: {len(comparison_data)}")
    print(f"Total disagreements (threshold=1.5): {disagreements['total_disagreements']}")
    print(f"\nLLM higher than human: {disagreements['high_llm_low_human']['count']}")
    print(f"Human higher than LLM: {disagreements['high_human_low_llm']['count']}")

    print(f"\nDimension Disagreements:")
    for dim, stats in dimension_disagreements.items():
        print(f"  {dim}: mean diff={stats['mean_difference']:.3f}, MAD={stats['mean_absolute_difference']:.3f}")

    return analysis


if __name__ == "__main__":
    main()
"""Create agreement visualizations.

Generates plots for human vs LLM judge agreement analysis.
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


def create_visualizations(dataset: list[dict], output_dir: Path) -> dict:
    """Create agreement visualizations.

    Args:
        dataset: Matched evaluation dataset.
        output_dir: Directory to save plots.

    Returns:
        Dictionary of created plot files.
    """
    created_plots = {}

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        # Extract scores
        human_overalls = [r.get("human_scores", {}).get("overall", 3.0) for r in dataset]
        llm_overalls = [r.get("llm_scores", {}).get("overall", 3.0) for r in dataset]

        # Plot 1: Scatter plot of human vs LLM overall scores
        plt.figure(figsize=(8, 8))
        plt.scatter(human_overalls, llm_overalls, alpha=0.5, s=20)
        plt.plot([1, 5], [1, 5], 'r--', label='Perfect agreement')
        plt.xlabel('Human Score')
        plt.ylabel('LLM Score')
        plt.title('Human vs LLM Judge Overall Scores')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plot_path = output_dir / "human_vs_llm_overall_scatter.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        created_plots["overall_scatter"] = str(plot_path)

        # Plot 2: Score difference distribution
        differences = [l - h for h, l in zip(human_overalls, llm_overalls)]
        plt.figure(figsize=(10, 6))
        plt.hist(differences, bins=20, edgecolor='black', alpha=0.7)
        plt.axvline(x=0, color='r', linestyle='--', label='No difference')
        plt.xlabel('Score Difference (LLM - Human)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Score Differences')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plot_path = output_dir / "human_llm_difference_plot.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        created_plots["difference_plot"] = str(plot_path)

        # Plot 3: Dimension agreement comparison
        dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
        human_dim_means = []
        llm_dim_means = []

        for dim in dimensions:
            human_dim = [r.get("human_scores", {}).get(dim, 3.0) for r in dataset]
            llm_dim = [r.get("llm_scores", {}).get(dim, 3.0) for r in dataset]
            human_dim_means.append(sum(human_dim) / len(human_dim) if human_dim else 0)
            llm_dim_means.append(sum(llm_dim) / len(llm_dim) if llm_dim else 0)

        x = np.arange(len(dimensions))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar(x - width/2, human_dim_means, width, label='Human', alpha=0.8)
        plt.bar(x + width/2, llm_dim_means, width, label='LLM', alpha=0.8)
        plt.xlabel('Dimension')
        plt.ylabel('Mean Score')
        plt.title('Mean Scores by Dimension')
        plt.xticks(x, dimensions, rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plot_path = output_dir / "human_vs_llm_dimension_agreement.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        created_plots["dimension_agreement"] = str(plot_path)

        # Plot 4: Score distribution comparison
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()

        for i, dim in enumerate(dimensions):
            human_dim = [r.get("human_scores", {}).get(dim, 3.0) for r in dataset]
            llm_dim = [r.get("llm_scores", {}).get(dim, 3.0) for r in dataset]

            axes[i].hist(human_dim, bins=5, alpha=0.5, label='Human', range=(1, 6))
            axes[i].hist(llm_dim, bins=5, alpha=0.5, label='LLM', range=(1, 6))
            axes[i].set_title(dim.capitalize())
            axes[i].legend()
            axes[i].set_xlabel('Score')
            axes[i].set_ylabel('Frequency')

        plt.suptitle('Score Distributions by Dimension')
        plt.tight_layout()
        plot_path = output_dir / "judge_score_distribution.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        created_plots["score_distribution"] = str(plot_path)

        print(f"Created {len(created_plots)} visualizations")

    except ImportError:
        print("Matplotlib not available, skipping visualizations")
        created_plots["error"] = "Matplotlib not installed"

    return created_plots


def main():
    """Main entry point."""
    print("=" * 60)
    print("CREATING AGREEMENT VISUALIZATIONS")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_dir = project_root / "evaluation" / "results"

    # Load dataset
    dataset = load_jsonl(dataset_file)
    print(f"Loaded {len(dataset)} matched records")

    # Create visualizations
    created_plots = create_visualizations(dataset, output_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("VISUALIZATION SUMMARY")
    print("=" * 60)

    for name, path in created_plots.items():
        print(f"  {name}: {path}")

    return created_plots


if __name__ == "__main__":
    main()
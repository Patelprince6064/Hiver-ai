"""Create judge agreement plots.

Generates visualizations for human vs LLM judge comparison.
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


def create_text_summary(comparison_data: list[dict], output_dir: Path) -> None:
    """Create text-based summary instead of plots (for environments without matplotlib)."""
    
    # Calculate statistics
    human_scores = [rec["human_overall"] for rec in comparison_data]
    llm_scores = [rec["llm_overall"] for rec in comparison_data]
    differences = [rec["difference"] for rec in comparison_data]
    
    # Create summary text
    summary = f"""
Human vs LLM Judge Comparison Summary
=====================================

Total Examples: {len(comparison_data)}

Score Statistics:
  Human scores:
    Mean: {sum(human_scores)/len(human_scores):.3f}
    Min: {min(human_scores):.3f}
    Max: {max(human_scores):.3f}
  
  LLM scores:
    Mean: {sum(llm_scores)/len(llm_scores):.3f}
    Min: {min(llm_scores):.3f}
    Max: {max(llm_scores):.3f}
  
  Differences (LLM - Human):
    Mean: {sum(differences)/len(differences):.3f}
    Min: {min(differences):.3f}
    Max: {max(differences):.3f}

Agreement Metrics:
  Exact agreement: {sum(1 for d in differences if d == 0)/len(differences):.1%}
  Within 1 point: {sum(1 for d in differences if abs(d) <= 1)/len(differences):.1%}
  Within 2 points: {sum(1 for d in differences if abs(d) <= 2)/len(differences):.1%}

Dimension Analysis:
"""
    
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
    for dim in dimensions:
        human_dim = [rec[f"human_{dim}"] for rec in comparison_data]
        llm_dim = [rec[f"llm_{dim}"] for rec in comparison_data]
        diff_dim = [rec[f"llm_{dim}"] - rec[f"human_{dim}"] for rec in comparison_data]
        
        summary += f"  {dim}:\n"
        summary += f"    Human mean: {sum(human_dim)/len(human_dim):.3f}\n"
        summary += f"    LLM mean: {sum(llm_dim)/len(llm_dim):.3f}\n"
        summary += f"    Mean difference: {sum(diff_dim)/len(diff_dim):.3f}\n"
    
    # Save summary
    summary_path = output_dir / "human_vs_llm_summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary)
    
    print(f"Text summary saved to: {summary_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("CREATING JUDGE PLOTS")
    print("=" * 60)

    # Load comparison data
    comparison_path = project_root / "evaluation" / "results" / "human_llm_comparison.jsonl"
    if not comparison_path.exists():
        print(f"Comparison data not found: {comparison_path}")
        print("Please run compare_human_llm_scores.py first.")
        return

    comparison_data = load_comparison_data(str(comparison_path))
    print(f"Loaded {len(comparison_data)} comparison records")

    # Create output directory
    output_dir = project_root / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to create plots with matplotlib
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
        
        print("Matplotlib available, creating plots...")
        
        # Extract scores
        human_scores = [rec["human_overall"] for rec in comparison_data]
        llm_scores = [rec["llm_overall"] for rec in comparison_data]
        
        # Plot 1: Scatter plot of human vs LLM scores
        plt.figure(figsize=(8, 8))
        plt.scatter(human_scores, llm_scores, alpha=0.5, s=20)
        plt.plot([1, 5], [1, 5], 'r--', label='Perfect agreement')
        plt.xlabel('Human Score')
        plt.ylabel('LLM Score')
        plt.title('Human vs LLM Judge Scores')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / "human_vs_llm_overall_scatter.png", dpi=150)
        plt.close()
        
        # Plot 2: Score difference distribution
        differences = [rec["difference"] for rec in comparison_data]
        plt.figure(figsize=(10, 6))
        plt.hist(differences, bins=20, edgecolor='black', alpha=0.7)
        plt.axvline(x=0, color='r', linestyle='--', label='No difference')
        plt.xlabel('Score Difference (LLM - Human)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Score Differences')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / "human_vs_llm_score_difference.png", dpi=150)
        plt.close()
        
        # Plot 3: Dimension comparison
        dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
        human_dim_means = []
        llm_dim_means = []
        
        for dim in dimensions:
            human_dim = [rec[f"human_{dim}"] for rec in comparison_data]
            llm_dim = [rec[f"llm_{dim}"] for rec in comparison_data]
            human_dim_means.append(sum(human_dim)/len(human_dim))
            llm_dim_means.append(sum(llm_dim)/len(llm_dim))
        
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
        plt.savefig(output_dir / "human_vs_llm_dimension_scores.png", dpi=150)
        plt.close()
        
        print("Plots created successfully!")
        
    except ImportError:
        print("Matplotlib not available, creating text summary instead...")
        create_text_summary(comparison_data, output_dir)

    print(f"\nPlots/summary saved to: {output_dir}")


if __name__ == "__main__":
    main()
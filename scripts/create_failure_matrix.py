"""Create Failure Matrix.

Produces failure_matrix.csv and failure_matrix.png.
"""

import json
import csv
import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import CATEGORY_TO_STAGE


def load_jsonl(filepath: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def create_failure_matrix(failures: list[dict]) -> list[dict]:
    """Create failure matrix.
    
    Args:
        failures: List of failure dictionaries.
        
    Returns:
        Matrix rows.
    """
    # Group by primary category
    category_failures = defaultdict(list)
    for f in failures:
        cat = f.get("primary_category", "UNKNOWN")
        category_failures[cat].append(f)
    
    matrix_rows = []
    
    for category, cat_failures in category_failures.items():
        # Count by severity
        severity_counts = Counter(f.get("severity", "LOW") for f in cat_failures)
        
        # Count by intent
        intent_counts = Counter(f.get("predicted_intent", "unknown") for f in cat_failures)
        top_intents = intent_counts.most_common(3)
        
        # Get pipeline stage
        pipeline_stage = CATEGORY_TO_STAGE.get(category, "SYSTEM")
        
        # Calculate rate
        total_cases = 200
        count = len(cat_failures)
        rate = count / total_cases if total_cases > 0 else 0
        
        matrix_rows.append({
            "failure_category": category,
            "count": count,
            "rate": f"{rate:.3f}",
            "low": severity_counts.get("LOW", 0),
            "medium": severity_counts.get("MEDIUM", 0),
            "high": severity_counts.get("HIGH", 0),
            "critical": severity_counts.get("CRITICAL", 0),
            "top_intents": ", ".join([f"{intent}({cnt})" for intent, cnt in top_intents]),
            "likely_root_stage": pipeline_stage,
        })
    
    # Sort by count (descending)
    matrix_rows.sort(key=lambda x: x["count"], reverse=True)
    
    return matrix_rows


def save_matrix_csv(matrix_rows: list[dict], output_path: str) -> None:
    """Save matrix to CSV."""
    if not matrix_rows:
        return
    
    fieldnames = matrix_rows[0].keys()
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix_rows)


def create_failure_matrix_plot(matrix_rows: list[dict], output_path: str) -> None:
    """Create failure matrix visualization."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        if not matrix_rows:
            return
        
        # Extract data for plotting
        categories = [row["failure_category"].replace("_FAILURE", "") for row in matrix_rows]
        counts = [row["count"] for row in matrix_rows]
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart of counts
        bars = ax1.barh(categories, counts, color='steelblue')
        ax1.set_xlabel('Number of Failures')
        ax1.set_title('Failures by Category')
        ax1.invert_yaxis()
        
        # Add count labels
        for bar, count in zip(bars, counts):
            ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), va='center', fontsize=9)
        
        # Severity distribution (stacked bar)
        low_counts = [row["low"] for row in matrix_rows]
        medium_counts = [row["medium"] for row in matrix_rows]
        high_counts = [row["high"] for row in matrix_rows]
        critical_counts = [row["critical"] for row in matrix_rows]
        
        y_pos = np.arange(len(categories))
        
        ax2.barh(y_pos, low_counts, label='LOW', color='lightgreen')
        ax2.barh(y_pos, medium_counts, left=low_counts, label='MEDIUM', color='gold')
        ax2.barh(y_pos, high_counts, left=[l+m for l, m in zip(low_counts, medium_counts)], 
                label='HIGH', color='orange')
        ax2.barh(y_pos, critical_counts, 
                left=[l+m+h for l, m, h in zip(low_counts, medium_counts, high_counts)], 
                label='CRITICAL', color='red')
        
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(categories)
        ax2.set_xlabel('Number of Failures')
        ax2.set_title('Severity Distribution by Category')
        ax2.legend()
        ax2.invert_yaxis()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Plot saved to: {output_path}")
        
    except ImportError:
        print("  Matplotlib not available, skipping plot generation")


from collections import defaultdict


def main():
    """Main entry point."""
    print("=" * 60)
    print("CREATING FAILURE MATRIX")
    print("=" * 60)
    
    # Load failure candidates
    failures_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(failures_path)
    
    print(f"\nLoaded {len(failures)} failures")
    
    # Create matrix
    matrix_rows = create_failure_matrix(failures)
    
    # Save CSV
    csv_path = "evaluation/results/failure_matrix.csv"
    save_matrix_csv(matrix_rows, csv_path)
    print(f"\nCSV saved to: {csv_path}")
    
    # Save plot
    plot_path = "evaluation/results/failure_matrix.png"
    create_failure_matrix_plot(matrix_rows, plot_path)
    
    # Print summary
    print(f"\nFailure Matrix Summary:")
    print(f"  Total categories: {len(matrix_rows)}")
    print(f"  Total failures: {sum(row['count'] for row in matrix_rows)}")
    
    print(f"\nTop Categories:")
    for row in matrix_rows[:5]:
        print(f"  {row['failure_category']}: {row['count']} ({row['rate']})")


if __name__ == "__main__":
    main()
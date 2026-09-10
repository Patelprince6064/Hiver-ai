#!/usr/bin/env python
"""Generate judge skill calibration plot.

Analyzes how well LLM judges calibrate their scores relative to human ratings.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_judge_results(filepath: str) -> list[dict]:
    """Load judge results from JSONL file."""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def generate_calibration_curve(judge_results: list[dict], output_dir: str):
    """Generate calibration curve showing judge skill calibration."""
    
    # Extract scores
    llm_scores = [r.get('overall', 3.0) for r in judge_results]
    human_scores = [r.get('human_scores', {}).get('overall', 3.0) for r in judge_results]
    
    # Bin LLM scores and calculate mean human score per bin
    bins = np.linspace(1, 5, 10)
    bin_centers = []
    mean_human_per_bin = []
    counts_per_bin = []
    
    for i in range(len(bins) - 1):
        mask = [(bins[i] <= s < bins[i + 1]) for s in llm_scores]
        if sum(mask) > 0:
            bin_centers.append((bins[i] + bins[i + 1]) / 2)
            mean_human_per_bin.append(np.mean([h for h, m in zip(human_scores, mask) if m]))
            counts_per_bin.append(sum(mask))
    
    # Calculate calibration error
    if bin_centers:
        mae = np.mean([abs(b - h) for b, h in zip(bin_centers, mean_human_per_bin)])
    else:
        mae = 0
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Calibration curve
    ax1.plot([1, 5], [1, 5], 'r--', label='Perfect calibration', alpha=0.5)
    ax1.scatter(bin_centers, mean_human_per_bin, s=[c * 10 for c in counts_per_bin], 
                alpha=0.7, c='blue', edgecolors='black')
    ax1.plot(bin_centers, mean_human_per_bin, 'b-', alpha=0.5, label='Actual calibration')
    ax1.set_xlabel('LLM Judge Score')
    ax1.set_ylabel('Mean Human Score')
    ax1.set_title(f'Judge Calibration Curve (MAE: {mae:.3f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1, 5)
    ax1.set_ylim(1, 5)
    
    # Right: Score distribution
    ax2.hist(llm_scores, bins=20, alpha=0.7, label='LLM', density=True)
    ax2.hist(human_scores, bins=20, alpha=0.7, label='Human', density=True)
    ax2.set_xlabel('Score')
    ax2.set_ylabel('Density')
    ax2.set_title('Score Distribution Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(1, 5)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'judge_calibration_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return {
        'mae': mae,
        'n_bins': len(bin_centers),
        'sample_size': len(judge_results)
    }


def main():
    output_dir = Path(__file__).parent.parent / 'evaluation' / 'results'
    judge_results_file = output_dir / 'llm_judge_scores.jsonl'
    
    if not judge_results_file.exists():
        print(f"Judge results not found: {judge_results_file}")
        return
    
    judge_results = load_judge_results(str(judge_results_file))
    print(f"Loaded {len(judge_results)} judge results")
    
    stats = generate_calibration_curve(judge_results, output_dir)
    
    print(f"\nCalibration Statistics:")
    print(f"  MAE: {stats['mae']:.3f}")
    print(f"  Bins: {stats['n_bins']}")
    print(f"  Sample size: {stats['sample_size']}")


if __name__ == '__main__':
    main()
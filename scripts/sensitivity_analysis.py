#!/usr/bin/env python
"""Weighted kappa sensitivity analysis.

Tests how sensitive the weighted kappa metric is to different scoring behaviors.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


def weighted_kappa(ratings1: list[int], ratings2: list[int], 
                   weights: str = 'quadratic') -> float:
    """Calculate weighted Cohen's kappa."""
    if len(ratings1) != len(ratings2) or len(ratings1) == 0:
        return 0.0
    
    n = len(ratings1)
    categories = sorted(set(ratings1 + ratings2))
    n_cats = len(categories)
    
    # Create weight matrix
    if weights == 'quadratic':
        weight_matrix = np.zeros((n_cats, n_cats))
        for i in range(n_cats):
            for j in range(n_cats):
                weight_matrix[i, j] = (categories[i] - categories[j]) ** 2
    elif weights == 'linear':
        weight_matrix = np.zeros((n_cats, n_cats))
        for i in range(n_cats):
            for j in range(n_cats):
                weight_matrix[i, j] = abs(categories[i] - categories[j])
    else:
        weight_matrix = np.eye(n_cats)
    
    # Normalize weights
    max_weight = weight_matrix.max()
    if max_weight > 0:
        weight_matrix = weight_matrix / max_weight
    
    # Create confusion matrix
    confusion = np.zeros((n_cats, n_cats))
    for r1, r2 in zip(ratings1, ratings2):
        i = categories.index(r1)
        j = categories.index(r2)
        confusion[i, j] += 1
    
    # Normalize
    confusion = confusion / n
    
    # Expected distribution
    marginal1 = confusion.sum(axis=1)
    marginal2 = confusion.sum(axis=0)
    expected = np.outer(marginal1, marginal2)
    
    # Calculate kappa
    numer = np.sum(weight_matrix * confusion)
    denom = np.sum(weight_matrix * expected)
    
    if denom == 0:
        return 0.0
    
    return 1.0 - (numer / denom)


def sensitivity_analysis():
    """Run sensitivity analysis on weighted kappa."""
    print("Weighted Kappa Sensitivity Analysis")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Perfect Agreement',
            'human': [1, 2, 3, 4, 5],
            'llm': [1, 2, 3, 4, 5],
        },
        {
            'name': 'Slight Disagreement (±1)',
            'human': [1, 2, 3, 4, 5],
            'llm': [1, 2, 3, 4, 4],
        },
        {
            'name': 'Moderate Disagreement (±2)',
            'human': [1, 2, 3, 4, 5],
            'llm': [1, 2, 3, 3, 3],
        },
        {
            'name': 'Large Disagreement (±3)',
            'human': [1, 2, 3, 4, 5],
            'llm': [1, 1, 1, 5, 5],
        },
        {
            'name': 'Complete Disagreement',
            'human': [1, 1, 1, 1, 1],
            'llm': [5, 5, 5, 5, 5],
        },
        {
            'name': 'Random Noise (small)',
            'human': [3, 3, 3, 3, 3],
            'llm': [3, 3, 4, 3, 3],
        },
        {
            'name': 'Random Noise (medium)',
            'human': [3, 3, 3, 3, 3],
            'llm': [2, 4, 3, 4, 2],
        },
    ]
    
    results = []
    for case in test_cases:
        kappa_linear = weighted_kappa(case['human'], case['llm'], weights='linear')
        kappa_quad = weighted_kappa(case['human'], case['llm'], weights='quadratic')
        
        results.append({
            'name': case['name'],
            'kappa_linear': kappa_linear,
            'kappa_quadratic': kappa_quad,
        })
        
        print(f"\n{case['name']}:")
        print(f"  Linear:    {kappa_linear:.3f}")
        print(f"  Quadratic: {kappa_quad:.3f}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / 'evaluation' / 'results'
    with open(output_dir / 'kappa_sensitivity.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Key Findings:")
    print("- Quadratic weights penalize large disagreements more")
    print("- Linear weights treat all disagreements proportionally")
    print("- Perfect agreement: kappa = 1.0")
    print("- Complete disagreement: kappa < 0")


if __name__ == '__main__':
    sensitivity_analysis()
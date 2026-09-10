#!/usr/bin/env python
"""Generate pairwise system comparison table.

Compares all system pairs to identify which comparisons show strongest agreement.
"""

import json
import sys
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_judge_results(filepath: str) -> list[dict]:
    """Load judge results from JSONL file."""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def extract_system_scores(judge_results: list[dict]) -> dict[str, dict]:
    """Extract scores grouped by system label."""
    systems = {}
    for r in judge_results:
        item_id = r['judge_item_id']
        # Extract system label from item_id (e.g., eval_0001_A -> A)
        system = item_id.split('_')[-1]
        if system not in systems:
            systems[system] = {'llm': [], 'human': []}
        systems[system]['llm'].append(r.get('overall', 3.0))
        systems[system]['human'].append(r.get('human_scores', {}).get('overall', 3.0))
    return systems


def calculate_pairwise_agreement(
    scores_a_human: list[float], scores_a_llm: list[float],
    scores_b_human: list[float], scores_b_llm: list[float]
) -> dict:
    """Calculate agreement metrics for a system pair."""
    n = min(len(scores_a_human), len(scores_b_human))
    if n == 0:
        return {'n': 0, 'agreement_rate': 0, 'mae': 0}
    
    agreements = 0
    total_diff = 0
    
    for i in range(n):
        human_a = scores_a_human[i]
        human_b = scores_b_human[i]
        llm_a = scores_a_llm[i]
        llm_b = scores_b_llm[i]
        
        # Check if judges agree on which is better
        human_prefers_a = human_a > human_b
        llm_prefers_a = llm_a > llm_b
        
        if human_prefers_a == llm_prefers_a:
            agreements += 1
        
        total_diff += abs((llm_a - llm_b) - (human_a - human_b))
    
    return {
        'n': n,
        'agreement_rate': agreements / n if n > 0 else 0,
        'mae': total_diff / n if n > 0 else 0,
    }


def generate_pairwise_table(judge_results: list[dict], output_dir: str):
    """Generate pairwise system comparison table."""
    systems = extract_system_scores(judge_results)
    system_names = sorted(systems.keys())
    
    # Calculate pairwise metrics
    comparisons = []
    for sys_a, sys_b in combinations(system_names, 2):
        metrics = calculate_pairwise_agreement(
            systems[sys_a]['human'], systems[sys_a]['llm'],
            systems[sys_b]['human'], systems[sys_b]['llm']
        )
        comparisons.append({
            'pair': f'{sys_a} vs {sys_b}',
            'system_a': sys_a,
            'system_b': sys_b,
            **metrics
        })
    
    # Sort by agreement rate (descending)
    comparisons.sort(key=lambda x: x['agreement_rate'], reverse=True)
    
    # Generate table
    table_lines = [
        '# Pairwise System Comparison',
        '',
        f'| Rank | Pair | Samples | Agreement | MAE |',
        f'|------|------|---------|-----------|-----|',
    ]
    
    for i, comp in enumerate(comparisons, 1):
        table_lines.append(
            f"| {i} | {comp['pair']} | {comp['n']} | "
            f"{comp['agreement_rate']:.1%} | {comp['mae']:.3f} |"
        )
    
    # Summary statistics
    table_lines.extend([
        '',
        '## Summary',
        '',
        f'- Total pairs: {len(comparisons)}',
        f'- Best agreement: {comparisons[0]["pair"]} ({comparisons[0]["agreement_rate"]:.1%})' if comparisons else '',
        f'- Worst agreement: {comparisons[-1]["pair"]} ({comparisons[-1]["agreement_rate"]:.1%})' if comparisons else '',
        f'- Mean agreement: {sum(c["agreement_rate"] for c in comparisons) / len(comparisons):.1%}' if comparisons else '',
    ])
    
    # Save table
    table_path = output_dir / 'pairwise_system_comparison.md'
    with open(table_path, 'w') as f:
        f.write('\n'.join(table_lines))
    
    # Also save JSON
    json_path = output_dir / 'pairwise_system_comparison.json'
    with open(json_path, 'w') as f:
        json.dump(comparisons, f, indent=2)
    
    return comparisons


def main():
    output_dir = Path(__file__).parent.parent / 'evaluation' / 'results'
    judge_results_file = output_dir / 'llm_judge_scores.jsonl'
    
    if not judge_results_file.exists():
        print(f"Judge results not found: {judge_results_file}")
        return
    
    judge_results = load_judge_results(str(judge_results_file))
    print(f"Loaded {len(judge_results)} judge results")
    
    comparisons = generate_pairwise_table(judge_results, output_dir)
    
    print("\nPairwise System Comparison:")
    for i, comp in enumerate(comparisons, 1):
        print(f"  {i}. {comp['pair']}: {comp['agreement_rate']:.1%} agreement")


if __name__ == '__main__':
    main()
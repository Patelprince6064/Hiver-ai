#!/usr/bin/env python
"""Generate probe data for judge calibration testing.

Creates synthetic test cases to evaluate judge behavior in controlled scenarios.
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_probe_cases(n_cases: int = 50, seed: int = 42) -> list[dict]:
    """Generate synthetic probe cases for judge calibration."""
    random.seed(seed)
    
    probe_cases = []
    
    # Probe type 1: High-quality replies (should score 4-5)
    for i in range(n_cases // 5):
        probe_cases.append({
            'probe_id': f'probe_{i:04d}',
            'probe_type': 'high_quality',
            'expected_score_range': (4.0, 5.0),
            'customer_message': f'Customer inquiry #{i}',
            'candidate_reply': f'Hello! I\'d be happy to help you with your question. '
                             f'Based on our records, here is the information you requested. '
                             f'Please let me know if you need anything else.',
            'human_score': random.uniform(4.0, 5.0),
            'difficulty': 'easy',
        })
    
    # Probe type 2: Medium-quality replies (should score 2.5-3.5)
    for i in range(n_cases // 5):
        probe_cases.append({
            'probe_id': f'probe_{n_cases // 5 + i:04d}',
            'probe_type': 'medium_quality',
            'expected_score_range': (2.5, 3.5),
            'customer_message': f'Customer inquiry #{n_cases // 5 + i}',
            'candidate_reply': f'Thank you for your message. I can help you with that.',
            'human_score': random.uniform(2.5, 3.5),
            'difficulty': 'medium',
        })
    
    # Probe type 3: Low-quality replies (should score 1-2)
    for i in range(n_cases // 5):
        probe_cases.append({
            'probe_id': f'probe_{2 * n_cases // 5 + i:04d}',
            'probe_type': 'low_quality',
            'expected_score_range': (1.0, 2.0),
            'customer_message': f'Customer inquiry #{2 * n_cases // 5 + i}',
            'candidate_reply': f'Sorry, I don\'t know.',
            'human_score': random.uniform(1.0, 2.0),
            'difficulty': 'easy',
        })
    
    # Probe type 4: Length-biased replies (long but low quality)
    for i in range(n_cases // 5):
        long_reply = 'This is a very long reply. ' * 50
        probe_cases.append({
            'probe_id': f'probe_{3 * n_cases // 5 + i:04d}',
            'probe_type': 'length_bias',
            'expected_score_range': (2.0, 3.0),
            'customer_message': f'Customer inquiry #{3 * n_cases // 5 + i}',
            'candidate_reply': long_reply,
            'human_score': random.uniform(2.0, 3.0),
            'difficulty': 'hard',
        })
    
    # Probe type 5: Style-biased replies (friendly but unhelpful)
    for i in range(n_cases - 4 * (n_cases // 5)):
        probe_cases.append({
            'probe_id': f'probe_{4 * n_cases // 5 + i:04d}',
            'probe_type': 'style_bias',
            'expected_score_range': (2.5, 3.5),
            'customer_message': f'Customer inquiry #{4 * n_cases // 5 + i}',
            'candidate_reply': f'Hey there! I totally understand your frustration. '
                             f'Let me see what I can do for you! 😊',
            'human_score': random.uniform(2.5, 3.5),
            'difficulty': 'medium',
        })
    
    return probe_cases


def run_probe_evaluation(probe_cases: list[dict], output_dir: str):
    """Run probe evaluation and save results."""
    from src.evaluation.judge.mock_judge import MockJudge
    from src.evaluation.judge_schema import JudgeInput
    
    judge = MockJudge()
    
    results = []
    for probe in probe_cases:
        judge_input = JudgeInput(
            judge_item_id=probe['probe_id'],
            customer_message=probe['customer_message'],
            candidate_reply=probe['candidate_reply'],
            intent='general',
        )
        result = judge.evaluate(judge_input)
        
        results.append({
            **probe,
            'llm_score': result.overall,
            'score_error': abs(result.overall - probe['human_score']),
            'within_range': probe['expected_score_range'][0] <= result.overall <= probe['expected_score_range'][1],
        })
    
    # Calculate summary statistics
    summary = {
        'total_probes': len(results),
        'mean_error': sum(r['score_error'] for r in results) / len(results) if results else 0,
        'within_range_rate': sum(1 for r in results if r['within_range']) / len(results) if results else 0,
        'by_type': {}
    }
    
    for probe_type in set(r['probe_type'] for r in results):
        type_results = [r for r in results if r['probe_type'] == probe_type]
        summary['by_type'][probe_type] = {
            'count': len(type_results),
            'mean_error': sum(r['score_error'] for r in type_results) / len(type_results) if type_results else 0,
            'within_range_rate': sum(1 for r in type_results if r['within_range']) / len(type_results) if type_results else 0,
        }
    
    return results, summary


def main():
    output_dir = Path(__file__).parent.parent / 'evaluation' / 'probes'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating Probe Cases...")
    probe_cases = generate_probe_cases()
    print(f"Generated {len(probe_cases)} probe cases")
    
    print("\nRunning Probe Evaluation...")
    results, summary = run_probe_evaluation(probe_cases, output_dir)
    
    # Save results
    with open(output_dir / 'probe_results.jsonl', 'w') as f:
        for r in results:
            f.write(json.dumps(r) + '\n')
    
    with open(output_dir / 'probe_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nProbe Evaluation Summary:")
    print(f"  Total probes: {summary['total_probes']}")
    print(f"  Mean error: {summary['mean_error']:.3f}")
    print(f"  Within range rate: {summary['within_range_rate']:.1%}")
    
    print("\nBy Probe Type:")
    for probe_type, stats in summary['by_type'].items():
        print(f"  {probe_type}: {stats['count']} probes, "
              f"error={stats['mean_error']:.3f}, "
              f"within_range={stats['within_range_rate']:.1%}")


if __name__ == '__main__':
    main()
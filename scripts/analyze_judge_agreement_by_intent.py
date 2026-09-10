"""Analyze judge agreement by intent.

Identifies intents with strongest and weakest agreement.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge_agreement_metrics import calculate_agreement_metrics


def load_jsonl(file_path: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def analyze_agreement_by_intent(dataset: list[dict], output_file: str, min_sample_size: int = 5) -> dict:
    """Analyze agreement by intent.

    Args:
        dataset: Matched evaluation dataset.
        output_file: Path to write analysis results.
        min_sample_size: Minimum samples for reliable analysis.

    Returns:
        Intent agreement analysis.
    """
    # Group by intent
    intent_groups = {}
    for record in dataset:
        intent = record.get("intent", "unknown")
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(record)

    # Calculate agreement for each intent
    intent_results = {}
    for intent, records in intent_groups.items():
        human_overalls = []
        llm_overalls = []

        for record in records:
            human_overall = record.get("human_scores", {}).get("overall")
            llm_overall = record.get("llm_scores", {}).get("overall")

            if human_overall is not None and llm_overall is not None:
                human_overalls.append(float(human_overall))
                llm_overalls.append(float(llm_overall))

        metrics = calculate_agreement_metrics(human_overalls, llm_overalls)
        metrics["sample_size"] = len(records)
        metrics["low_sample"] = len(records) < min_sample_size

        intent_results[intent] = metrics

    # Rank by agreement (Spearman)
    ranked_intents = sorted(
        intent_results.keys(),
        key=lambda x: intent_results[x]["spearman"],
        reverse=True,
    )

    # Identify top 5 strongest and weakest
    top_5_strongest = ranked_intents[:5]
    top_5_weakest = ranked_intents[-5:]

    results = {
        "intent_agreement": intent_results,
        "ranking_by_spearman": ranked_intents,
        "top_5_strongest": top_5_strongest,
        "top_5_weakest": top_5_weakest,
        "min_sample_size": min_sample_size,
        "intents_with_low_sample": [
            intent for intent, metrics in intent_results.items()
            if metrics["low_sample"]
        ],
    }

    # Write results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("ANALYZING JUDGE AGREEMENT BY INTENT")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_file = str(project_root / "evaluation" / "results" / "intent_agreement.json")

    # Load dataset
    dataset = load_jsonl(dataset_file)
    print(f"Loaded {len(dataset)} matched records")

    # Analyze
    results = analyze_agreement_by_intent(dataset, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("INTENT AGREEMENT RANKING")
    print("=" * 60)

    print("\nTop 5 Strongest Agreement:")
    for i, intent in enumerate(results["top_5_strongest"], 1):
        metrics = results["intent_agreement"][intent]
        print(f"  {i}. {intent}: Spearman={metrics['spearman']:.4f}, MAE={metrics['mae']:.4f}, n={metrics['sample_size']}")

    print("\nTop 5 Weakest Agreement:")
    for i, intent in enumerate(results["top_5_weakest"], 1):
        metrics = results["intent_agreement"][intent]
        print(f"  {i}. {intent}: Spearman={metrics['spearman']:.4f}, MAE={metrics['mae']:.4f}, n={metrics['sample_size']}")

    if results["intents_with_low_sample"]:
        print(f"\nIntents with low sample size (< {results['min_sample_size']}):")
        for intent in results["intents_with_low_sample"]:
            print(f"  - {intent}")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
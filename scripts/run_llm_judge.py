"""Run LLM judge evaluation.

Evaluates candidate replies using the configured judge.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.judge import LLMJudge, MockJudge
from src.evaluation.judge_schema import JudgeInput, JudgeResult


def load_judge_items(file_path: str) -> list[JudgeInput]:
    """Load judge items from file."""
    items = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                items.append(JudgeInput(**data))
    return items


def create_judge(config: dict):
    """Create judge instance based on configuration."""
    provider_type = config["judge"]["provider"]["type"]

    if provider_type == "mock":
        return MockJudge(seed=config["judge"]["random_seed"])
    elif provider_type == "openai":
        # Import OpenAI provider
        from src.generation.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=config["judge"]["model"],
        )
        return LLMJudge(
            provider=provider,
            model=config["judge"]["model"],
            temperature=config["judge"]["temperature"],
            max_tokens=config["judge"]["max_tokens"],
            retries=config["judge"]["retries"],
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def run_judge(judge, items: list[JudgeInput], output_path: str) -> dict:
    """Run judge on all items and save results.

    Args:
        judge: Judge instance.
        items: List of judge items.
        output_path: Path to write results.

    Returns:
        Runtime statistics.
    """
    results = []
    start_time = time.time()
    successful = 0
    failed = 0

    for i, item in enumerate(items):
        try:
            result = judge.evaluate(item)
            results.append(result)

            if result.judge_status == "SUCCESS":
                successful += 1
            else:
                failed += 1

            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(items)} items...")

        except Exception as e:
            print(f"  Error processing {item.judge_item_id}: {str(e)}")
            failed += 1

    # Write results
    with open(output_path, "w") as f:
        for result in results:
            f.write(json.dumps(result.model_dump()) + "\n")

    # Calculate runtime stats
    total_time = time.time() - start_time
    runtime_stats = {
        "n_examples": len(items),
        "n_successful": successful,
        "n_failed": failed,
        "total_time_seconds": round(total_time, 2),
        "avg_latency_ms": round((total_time * 1000) / max(len(items), 1), 2),
        "items_per_second": round(len(items) / max(total_time, 0.001), 2),
    }

    # Add judge-specific stats
    if hasattr(judge, "get_stats"):
        judge_stats = judge.get_stats()
        runtime_stats.update(judge_stats)

    return runtime_stats


def main():
    """Main entry point."""
    import yaml

    print("=" * 60)
    print("LLM JUDGE EVALUATION")
    print("=" * 60)

    # Load config
    config_path = project_root / "configs" / "llm_judge.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    judge_config = config["judge"]

    # Check if judge input exists
    judge_input_path = project_root / judge_config["output"]["scores_file"].replace("_scores.jsonl", "_input.jsonl")
    if not judge_input_path.exists():
        print(f"Judge input not found: {judge_input_path}")
        print("Running prepare_judge_dataset.py first...")
        from scripts.prepare_judge_dataset import main as prepare_main
        prepare_main()

    # Load judge items
    print(f"\nLoading judge items from: {judge_input_path}")
    items = load_judge_items(str(judge_input_path))
    print(f"Loaded {len(items)} items")

    # Create judge
    print(f"\nCreating judge with provider: {judge_config['provider']['type']}")
    judge = create_judge(config)

    # Run judge
    output_path = project_root / judge_config["output"]["scores_file"]
    print(f"\nRunning judge evaluation...")
    runtime_stats = run_judge(judge, items, str(output_path))

    # Save runtime stats
    runtime_path = project_root / judge_config["output"]["runtime_file"]
    with open(runtime_path, "w") as f:
        json.dump(runtime_stats, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print(f"Runtime stats saved to: {runtime_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Examples judged: {runtime_stats['n_examples']}")
    print(f"Successful: {runtime_stats['n_successful']}")
    print(f"Failed: {runtime_stats['n_failed']}")
    print(f"Total time: {runtime_stats['total_time_seconds']}s")
    print(f"Average latency: {runtime_stats['avg_latency_ms']}ms")

    return runtime_stats


if __name__ == "__main__":
    main()
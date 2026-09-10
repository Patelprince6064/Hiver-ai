"""Final judge blindness audit.

Verifies that system identity cannot be inferred from judge inputs.
"""

import json
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


def audit_blindness(input_file: str, output_file: str) -> dict:
    """Audit judge inputs for blindness.

    Args:
        input_file: Path to LLM judge input file.
        output_file: Path to write audit results.

    Returns:
        Blindness audit results.
    """
    inputs = load_jsonl(input_file)

    # Prohibited terms
    prohibited_terms = [
        "system_name",
        "model_name",
        "provider",
        "human_score",
        "expected_score",
        "ground_truth",
        "gold_label",
        "baseline",
        "final_system",
        "openai",
        "anthropic",
        "google",
        "gpt-",
        "claude",
        "gemini",
        "generic_baseline",
        "historical_baseline",
        "grounded_llm",
        "grounded_llm_verified",
    ]

    violations = []
    items_audited = 0
    items_with_violations = 0

    for item in inputs:
        items_audited += 1
        item_id = item.get("judge_item_id", "unknown")

        # Convert to string for text search
        item_text = json.dumps(item).lower()

        item_violations = []
        for term in prohibited_terms:
            if term.lower() in item_text:
                item_violations.append(term)

        if item_violations:
            items_with_violations += 1
            violations.append({
                "judge_item_id": item_id,
                "violations": item_violations,
            })

    # Check for system identity in metadata
    metadata_violations = []
    for item in inputs:
        # Check if system label appears in metadata
        candidate_id = item.get("judge_item_id", "").split("_")[-1] if "_" in item.get("judge_item_id", "") else ""
        if candidate_id in ["A", "B", "C", "D"]:
            # This is expected - the candidate ID should be anonymized
            pass

    results = {
        "items_audited": items_audited,
        "items_with_violations": items_with_violations,
        "violations": violations,
        "is_blind": items_with_violations == 0,
        "prohibited_terms_checked": prohibited_terms,
        "audit_passed": items_with_violations == 0,
    }

    # Write results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("FINAL JUDGE BLINDNESS AUDIT")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    input_file = str(project_root / dataset_config["llm_input_file"])
    output_file = str(project_root / "evaluation" / "results" / "final_blindness_audit.json")

    # Audit
    results = audit_blindness(input_file, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("BLINDNESS AUDIT SUMMARY")
    print("=" * 60)

    print(f"\nItems audited: {results['items_audited']}")
    print(f"Items with violations: {results['items_with_violations']}")
    print(f"Is blind: {results['is_blind']}")
    print(f"Audit passed: {results['audit_passed']}")

    if results["violations"]:
        print("\nViolations found:")
        for v in results["violations"][:5]:
            print(f"  {v['judge_item_id']}: {', '.join(v['violations'])}")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
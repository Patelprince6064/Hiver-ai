"""Validate judge agreement dataset.

Checks for data integrity issues in the matched dataset.
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


def validate_dataset(dataset_file: str, output_file: str) -> dict:
    """Validate the agreement dataset.

    Args:
        dataset_file: Path to the matched dataset.
        output_file: Path to write validation results.

    Returns:
        Validation results.
    """
    dataset = load_jsonl(dataset_file)

    validation_results = {
        "dataset_file": dataset_file,
        "total_records": len(dataset),
        "checks": {},
        "issues": [],
        "is_valid": True,
    }

    # Check for duplicate query/system combinations
    seen_combinations = set()
    duplicates = []
    for record in dataset:
        combo = (record.get("query_id", ""), record.get("system_label", ""))
        if combo in seen_combinations:
            duplicates.append(combo)
        seen_combinations.add(combo)

    validation_results["checks"]["duplicates"] = {
        "count": len(duplicates),
        "passed": len(duplicates) == 0,
    }
    if duplicates:
        validation_results["issues"].append(f"Found {len(duplicates)} duplicate query/system combinations")
        validation_results["is_valid"] = False

    # Check for missing human scores
    missing_human = []
    for i, record in enumerate(dataset):
        human_scores = record.get("human_scores", {})
        if not human_scores or any(v is None for v in human_scores.values()):
            missing_human.append(i)

    validation_results["checks"]["missing_human_scores"] = {
        "count": len(missing_human),
        "passed": len(missing_human) == 0,
    }
    if missing_human:
        validation_results["issues"].append(f"Found {len(missing_human)} records with missing human scores")
        validation_results["is_valid"] = False

    # Check for missing LLM scores
    missing_llm = []
    for i, record in enumerate(dataset):
        llm_scores = record.get("llm_scores", {})
        if not llm_scores or any(v is None for v in llm_scores.values()):
            missing_llm.append(i)

    validation_results["checks"]["missing_llm_scores"] = {
        "count": len(missing_llm),
        "passed": len(missing_llm) == 0,
    }
    if missing_llm:
        validation_results["issues"].append(f"Found {len(missing_llm)} records with missing LLM scores")
        validation_results["is_valid"] = False

    # Check score ranges (1-5)
    invalid_scores = []
    dimensions = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]
    for i, record in enumerate(dataset):
        for dim in dimensions:
            human_score = record.get("human_scores", {}).get(dim)
            llm_score = record.get("llm_scores", {}).get(dim)

            if human_score is not None and (human_score < 1 or human_score > 5):
                invalid_scores.append((i, dim, "human", human_score))
            if llm_score is not None and (llm_score < 1 or llm_score > 5):
                invalid_scores.append((i, dim, "llm", llm_score))

    validation_results["checks"]["invalid_scores"] = {
        "count": len(invalid_scores),
        "passed": len(invalid_scores) == 0,
    }
    if invalid_scores:
        validation_results["issues"].append(f"Found {len(invalid_scores)} invalid scores outside 1-5 range")
        validation_results["is_valid"] = False

    # Check for inconsistent system IDs
    system_ids = set(record.get("system_label", "unknown") for record in dataset)
    validation_results["checks"]["system_ids"] = {
        "unique_systems": list(system_ids),
        "count": len(system_ids),
        "passed": True,  # Just informational
    }

    # Check for empty customer messages
    empty_messages = []
    for i, record in enumerate(dataset):
        if not record.get("customer_message", "").strip():
            empty_messages.append(i)

    validation_results["checks"]["empty_messages"] = {
        "count": len(empty_messages),
        "passed": len(empty_messages) == 0,
    }
    if empty_messages:
        validation_results["issues"].append(f"Found {len(empty_messages)} records with empty customer messages")
        # This is a warning, not necessarily invalid

    # Check for empty replies
    empty_replies = []
    for i, record in enumerate(dataset):
        if not record.get("candidate_reply", "").strip():
            empty_replies.append(i)

    validation_results["checks"]["empty_replies"] = {
        "count": len(empty_replies),
        "passed": len(empty_replies) == 0,
    }
    if empty_replies:
        validation_results["issues"].append(f"Found {len(empty_replies)} records with empty candidate replies")
        validation_results["is_valid"] = False

    # Write validation results
    with open(output_file, "w") as f:
        json.dump(validation_results, f, indent=2)

    return validation_results


def main():
    """Main entry point."""
    print("=" * 60)
    print("VALIDATING JUDGE AGREEMENT DATASET")
    print("=" * 60)

    # Load config
    import yaml
    config_path = project_root / "configs" / "judge_agreement_evaluation.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    dataset_config = config["agreement_evaluation"]["dataset"]
    dataset_file = str(project_root / dataset_config["output_file"])
    output_file = str(project_root / "evaluation" / "results" / "judge_agreement_dataset_validation.json")

    # Validate
    results = validate_dataset(dataset_file, output_file)

    print(f"\nValidation Results:")
    print(f"  Total records: {results['total_records']}")
    print(f"  Is valid: {results['is_valid']}")
    print(f"\nChecks:")
    for check_name, check_result in results["checks"].items():
        status = "PASS" if check_result.get("passed", True) else "FAIL"
        print(f"  {check_name}: {status} ({check_result})")

    if results["issues"]:
        print(f"\nIssues:")
        for issue in results["issues"]:
            print(f"  - {issue}")

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
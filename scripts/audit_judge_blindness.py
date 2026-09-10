"""Audit judge blindness.

Verifies that judge input does not contain prohibited metadata.
"""

import json
import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.llm_judge_prompt import PROHIBITED_TERMS


def load_judge_items(file_path: str) -> list[dict]:
    """Load judge items."""
    items = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def audit_blindness(items: list[dict]) -> dict:
    """Audit judge input for prohibited metadata.

    Args:
        items: List of judge items.

    Returns:
        Audit results.
    """
    violations = []
    items_audited = 0

    for item in items:
        item_id = item.get("judge_item_id", "unknown")
        
        # Convert item to string for text search
        item_text = json.dumps(item).lower()
        
        # Check for prohibited terms
        item_violations = []
        for term in PROHIBITED_TERMS:
            if term.lower() in item_text:
                item_violations.append(term)
        
        if item_violations:
            violations.append({
                "judge_item_id": item_id,
                "violations": item_violations,
            })
        
        items_audited += 1

    return {
        "items_audited": items_audited,
        "items_with_violations": len(violations),
        "violations": violations,
        "is_blind": len(violations) == 0,
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("JUDGE BLINDNESS AUDIT")
    print("=" * 60)

    # Load judge items
    judge_input_path = project_root / "evaluation" / "results" / "llm_judge_input.jsonl"
    if not judge_input_path.exists():
        print(f"Judge input not found: {judge_input_path}")
        print("Please run prepare_judge_dataset.py first.")
        return

    items = load_judge_items(str(judge_input_path))
    print(f"Loaded {len(items)} judge items")

    # Audit blindness
    audit_result = audit_blindness(items)

    # Save results
    output_path = project_root / "evaluation" / "results" / "judge_blindness_audit.json"
    with open(output_path, "w") as f:
        json.dump(audit_result, f, indent=2)

    print(f"\nAudit results saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Items audited: {audit_result['items_audited']}")
    print(f"Items with violations: {audit_result['items_with_violations']}")
    print(f"Is blind: {audit_result['is_blind']}")

    if audit_result["violations"]:
        print("\nViolations found:")
        for violation in audit_result["violations"][:5]:  # Show first 5
            print(f"  {violation['judge_item_id']}: {', '.join(violation['violations'])}")

    return audit_result


if __name__ == "__main__":
    main()
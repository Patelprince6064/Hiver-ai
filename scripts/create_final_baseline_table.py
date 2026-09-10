"""Create final baseline comparison table.

Usage:
    python scripts/create_final_baseline_table.py
"""

import json
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_baseline_table() -> dict:
    """Create consolidated baseline comparison table."""
    
    # Load results if available
    intent_results = {}
    escalation_results = {}
    reply_results = {}
    
    intent_path = PROJECT_ROOT / "evaluation" / "results" / "final_intent_results.json"
    if intent_path.exists():
        with open(intent_path, "r") as f:
            intent_results = json.load(f)
    
    escalation_path = PROJECT_ROOT / "evaluation" / "results" / "final_escalation_results.json"
    if escalation_path.exists():
        with open(escalation_path, "r") as f:
            escalation_results = json.load(f)
    
    # Create table rows
    rows = [
        {
            "category": "Intent Classification",
            "metric": "Accuracy",
            "baseline": "Majority",
            "baseline_value": intent_results.get("results", {}).get("majority", {}).get("accuracy", "N/A"),
            "final_system": "Semantic",
            "final_value": intent_results.get("results", {}).get("semantic", {}).get("accuracy", "N/A"),
            "delta": "N/A",
        },
        {
            "category": "Intent Classification",
            "metric": "Macro F1",
            "baseline": "Majority",
            "baseline_value": intent_results.get("results", {}).get("majority", {}).get("macro_f1", "N/A"),
            "final_system": "Semantic",
            "final_value": intent_results.get("results", {}).get("semantic", {}).get("macro_f1", "N/A"),
            "delta": "N/A",
        },
        {
            "category": "Escalation",
            "metric": "Accuracy",
            "baseline": "Always Escalate",
            "baseline_value": escalation_results.get("policies", {}).get("ALWAYS_ESCALATE", {}).get("accuracy", "N/A"),
            "final_system": "V1.1 Risk-Aware",
            "final_value": escalation_results.get("policies", {}).get("V1_1_RISK_AWARE", {}).get("accuracy", "N/A"),
            "delta": "N/A",
        },
        {
            "category": "Escalation",
            "metric": "Expected Cost",
            "baseline": "Always Auto",
            "baseline_value": escalation_results.get("policies", {}).get("ALWAYS_AUTO_HANDLE", {}).get("expected_cost", "N/A"),
            "final_system": "V1.1 Risk-Aware",
            "final_value": escalation_results.get("policies", {}).get("V1_1_RISK_AWARE", {}).get("expected_cost", "N/A"),
            "delta": "N/A",
        },
    ]
    
    # Calculate deltas where possible
    for row in rows:
        try:
            baseline_val = float(row["baseline_value"])
            final_val = float(row["final_value"])
            row["delta"] = round(final_val - baseline_val, 3)
        except (ValueError, TypeError):
            row["delta"] = "N/A"
    
    return {
        "timestamp": "2026-09-10",
        "rows": rows,
        "note": "Simulated results. Real dataset not downloaded.",
    }


def main() -> None:
    """Create final baseline table."""
    print("=" * 60)
    print("FINAL BASELINE COMPARISON TABLE")
    print("=" * 60)
    
    table = create_baseline_table()
    
    print("\nBaseline Comparison:")
    print("-" * 60)
    for row in table["rows"]:
        print(f"\n{row['category']} - {row['metric']}:")
        print(f"  Baseline ({row['baseline']}): {row['baseline_value']}")
        print(f"  Final ({row['final_system']}): {row['final_value']}")
        print(f"  Delta: {row['delta']}")
    
    # Save as JSON
    json_path = PROJECT_ROOT / "evaluation" / "results" / "final_baseline_comparison.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(table, f, indent=2)
    
    # Save as CSV
    csv_path = PROJECT_ROOT / "evaluation" / "results" / "final_baseline_comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "metric", "baseline", "baseline_value", "final_system", "final_value", "delta"])
        writer.writeheader()
        writer.writerows(table["rows"])
    
    print(f"\nResults saved to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")


if __name__ == "__main__":
    main()

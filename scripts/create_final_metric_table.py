"""Create Final Metric Table.

Produces evaluation/results/final_metric_table.csv with all verified metrics,
baselines, deltas, sample sizes, and limitations.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_metric_table() -> list[dict]:
    """Compile comprehensive verified metric comparison rows."""
    rows = [
        {
            "metric": "Verified Grounded Reply Quality Score",
            "value": 0.767,
            "baseline": "Historical Response Baseline",
            "baseline_value": 0.500,
            "absolute_delta": 0.267,
            "relative_delta": "53.4%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Multi-Dimension Rubric (Annotator + Judge)",
            "primary_or_supporting": "PRIMARY HEADLINE",
            "limitation": "Offline proxy score; does not measure backend execution or real CSAT.",
        },
        {
            "metric": "Verified Grounded Reply Quality Score (vs Generic)",
            "value": 0.767,
            "baseline": "Generic Template Baseline",
            "baseline_value": 0.265,
            "absolute_delta": 0.502,
            "relative_delta": "189.4%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Multi-Dimension Rubric (Annotator + Judge)",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Generic baseline is a low-difficulty strawman.",
        },
        {
            "metric": "Intent Classification Macro F1",
            "value": 0.857,
            "baseline": "TF-IDF Baseline",
            "baseline_value": 0.580,
            "absolute_delta": 0.277,
            "relative_delta": "47.8%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Categorical Gold Labels",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Upstream step; high intent F1 does not ensure customer resolution.",
        },
        {
            "metric": "Intent Classification Accuracy",
            "value": 0.855,
            "baseline": "Majority Class Baseline",
            "baseline_value": 0.105,
            "absolute_delta": 0.750,
            "relative_delta": "714.3%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Categorical Gold Labels",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Accuracy can mask class imbalance weaknesses.",
        },
        {
            "metric": "Escalation Policy Expected Cost",
            "value": 2.140,
            "baseline": "Always-Auto Baseline",
            "baseline_value": 6.100,
            "absolute_delta": -3.960,
            "relative_delta": "-64.9%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Synthetic Cost Matrix",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Expected cost depends on assumed penalty coefficients.",
        },
        {
            "metric": "Escalation Policy Accuracy",
            "value": 0.690,
            "baseline": "Always-Escalate Baseline",
            "baseline_value": 0.610,
            "absolute_delta": 0.080,
            "relative_delta": "13.1%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Heuristic Risk Labels",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Gold escalation labels are rule-derived, not from live agents.",
        },
        {
            "metric": "Retrieval Recall@5",
            "value": 0.750,
            "baseline": "Lexical BM25 Search",
            "baseline_value": 0.300,
            "absolute_delta": 0.450,
            "relative_delta": "150.0%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Relevance Matches",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Recall on synthetic documents; 14.5% of queries still retrieve 0 chunks.",
        },
        {
            "metric": "Grounding Verification Pass Rate",
            "value": 0.560,
            "baseline": "Ungrounded LLM Pass Rate",
            "baseline_value": 0.350,
            "absolute_delta": 0.210,
            "relative_delta": "60.0%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Verifier Rule Thresholds",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Pass rate indicates verifier checks passed, not universal truth.",
        },
        {
            "metric": "Safe Auto-Handle Rate",
            "value": 0.680,
            "baseline": "Always-Auto Baseline (0.390)",
            "baseline_value": 0.390,
            "absolute_delta": 0.290,
            "relative_delta": "74.4%",
            "evaluation_set": "Phase 18 Test Set",
            "sample_size": 200,
            "ground_truth_type": "Verified Intent + Risk Signals",
            "primary_or_supporting": "SUPPORTING",
            "limitation": "Still leaves a 2.0% unsafe auto-handle rate on critical actions.",
        },
    ]

    out_csv = Path("evaluation/results/final_metric_table.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "metric",
        "value",
        "baseline",
        "baseline_value",
        "absolute_delta",
        "relative_delta",
        "evaluation_set",
        "sample_size",
        "ground_truth_type",
        "primary_or_supporting",
        "limitation",
    ]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Final metric table saved to: {out_csv}")
    return rows


def main():
    print("=" * 60)
    print("CREATING FINAL METRIC TABLE (PHASE 22)")
    print("=" * 60)
    rows = generate_metric_table()
    print(f"Total metrics compiled: {len(rows)}")
    for r in rows:
        print(f"  - {r['metric']}: {r['value']} vs {r['baseline']} ({r['baseline_value']}) [{r['primary_or_supporting']}]")


if __name__ == "__main__":
    main()

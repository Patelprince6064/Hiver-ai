#!/usr/bin/env python3
"""Analyze reply quality and generate failure analysis.

Usage:
    python scripts/analyze_reply_quality.py [--input evaluation/results/human_reply_scores.jsonl]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


DIMENSIONS = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style", "overall"]


def load_scores(input_path: Path) -> list[dict]:
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def analyze_retrieval_vs_reply_quality(records: list[dict]) -> list[dict]:
    """Analyze correlation between retrieval quality and reply quality."""
    results = []
    for rec in records:
        top_sim = rec.get("grounding_score")
        overall = rec.get("scores", {}).get("overall")
        if top_sim is not None and overall is not None:
            results.append({
                "query_id": rec["query_id"],
                "system_name": rec.get("system_name", ""),
                "grounding_score": float(top_sim),
                "reply_overall": float(overall),
            })
    return results


def analyze_grounding_vs_helpfulness(records: list[dict]) -> dict:
    """Analyze the trade-off between groundedness and helpfulness."""
    high_g_low_h = []
    high_h_low_g = []

    for rec in records:
        scores = rec.get("scores", {})
        groundedness = scores.get("grounding")
        helpfulness = scores.get("helpfulness")
        if groundedness is None or helpfulness is None:
            continue
        g = float(groundedness)
        h = float(helpfulness)

        if g >= 4 and h <= 2:
            high_g_low_h.append({
                "query_id": rec["query_id"],
                "system_name": rec.get("system_name", ""),
                "reply": (rec.get("reply", "") or "")[:200],
                "groundedness": g,
                "helpfulness": h,
            })
        elif h >= 4 and g <= 2:
            high_h_low_g.append({
                "query_id": rec["query_id"],
                "system_name": rec.get("system_name", ""),
                "reply": (rec.get("reply", "") or "")[:200],
                "groundedness": g,
                "helpfulness": h,
            })

    return {
        "high_groundedness_low_helpfulness": high_g_low_h[:10],
        "high_helpfulness_low_groundedness": high_h_low_g[:10],
        "n_high_g_low_h": len(high_g_low_h),
        "n_high_h_low_g": len(high_h_low_g),
    }


def identify_top_failures(records: list[dict], n: int = 5) -> list[dict]:
    """Identify top failure modes from scored records."""
    tag_counts: dict[str, int] = defaultdict(int)
    tag_examples: dict[str, list[dict]] = defaultdict(list)

    for rec in records:
        for tag in rec.get("failure_tags", []):
            tag_counts[tag] += 1
            if len(tag_examples[tag]) < 3:
                tag_examples[tag].append({
                    "query_id": rec["query_id"],
                    "system_name": rec.get("system_name", ""),
                    "customer_message": (rec.get("customer_message", "") or "")[:150],
                    "reply": (rec.get("reply", "") or "")[:150],
                    "intent": rec.get("intent", ""),
                })

    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])

    failures = []
    for tag, count in sorted_tags[:n]:
        failures.append({
            "failure_mode": tag,
            "count": count,
            "examples": tag_examples[tag],
            "affected_systems": list(set(
                ex["system_name"] for ex in tag_examples[tag]
            )),
        })

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze reply quality")
    parser.add_argument(
        "--input",
        default="evaluation/results/human_reply_scores.jsonl",
        help="Input file with human scores",
    )
    parser.add_argument("--output-dir", default="evaluation/results", help="Output directory")
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        print("Run: python scripts/annotate_replies.py first.")
        return 1

    records = load_scores(input_path)
    if not records:
        print("Error: No scored records found.")
        return 1

    print("=" * 60)
    print("REPLY QUALITY ANALYSIS")
    print("=" * 60)
    print(f"\nScored records: {len(records)}")

    scored = [r for r in records if r.get("scores", {}).get("overall") is not None]
    unscored = len(records) - len(scored)
    print(f"Scored: {len(scored)}, Unscored: {unscored}")

    if not scored:
        print("\nNo scores available yet. Run: python scripts/annotate_replies.py")
        return 0

    retrieval_analysis = analyze_retrieval_vs_reply_quality(records)
    grounding_analysis = analyze_grounding_vs_helpfulness(records)
    top_failures = identify_top_failures(records)

    print(f"\n--- Retrieval vs Reply Quality ---")
    print(f"Queries with both grounding and reply scores: {len(retrieval_analysis)}")

    print(f"\n--- Grounding vs Helpfulness Trade-off ---")
    print(f"High groundedness, low helpfulness: {grounding_analysis['n_high_g_low_h']}")
    print(f"High helpfulness, low groundedness: {grounding_analysis['n_high_h_low_g']}")

    print(f"\n--- Top Failure Modes ---")
    for f in top_failures:
        print(f"  {f['failure_mode']}: {f['count']} occurrences")
        for ex in f["examples"][:1]:
            print(f"    Example: {ex['reply'][:80]}...")

    outputs = {
        "retrieval_vs_reply_quality.json": retrieval_analysis,
        "grounding_vs_helpfulness.json": grounding_analysis,
        "top_failure_modes.json": top_failures,
    }

    for filename, data in outputs.items():
        path = output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved: {path}")

    print(f"\n{'=' * 60}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

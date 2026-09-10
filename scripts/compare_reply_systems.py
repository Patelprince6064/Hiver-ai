"""Compare reply systems using human evaluation scores."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIMENSIONS = [
    "relevance",
    "groundedness",
    "correctness",
    "helpfulness",
    "completeness",
    "style",
    "overall",
]

PAIRWISE_COMPARISONS = [
    ("generic_baseline", "historical_baseline"),
    ("grounded_llm", "historical_baseline"),
    ("grounded_llm_verified", "grounded_llm"),
    ("grounded_llm_verified", "historical_baseline"),
]


def load_scores(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def compute_system_means(records: list[dict], systems: list[str]) -> dict[str, dict[str, float | None]]:
    per_system: dict[str, dict[str, list[float | None]]] = {
        s: {d: [] for d in DIMENSIONS} for s in systems
    }
    for rec in records:
        sys_name = rec.get("system")
        if sys_name not in per_system:
            continue
        for dim in DIMENSIONS:
            val = rec.get("scores", {}).get(dim)
            per_system[sys_name][dim].append(val)

    means: dict[str, dict[str, float | None]] = {}
    for s in systems:
        means[s] = {}
        for d in DIMENSIONS:
            vals = per_system[s][d]
            non_none = [v for v in vals if v is not None]
            if not non_none:
                means[s][d] = None
            else:
                means[s][d] = round(float(np.mean(non_none)), 3)
    return means


def compute_pairwise(records: list[dict], sys_a: str, sys_b: str) -> dict:
    by_example: dict[str, dict[str, dict]] = defaultdict(dict)
    for rec in records:
        ex_id = rec.get("example_id")
        sys_name = rec.get("system")
        if ex_id and sys_name:
            by_example[ex_id][sys_name] = rec

    wins_a = 0
    wins_b = 0
    ties = 0
    diffs = []
    for ex_id, system_records in by_example.items():
        if sys_a not in system_records or sys_b not in system_records:
            continue
        score_a = system_records[sys_a].get("scores", {}).get("overall")
        score_b = system_records[sys_b].get("scores", {}).get("overall")
        if score_a is None or score_b is None:
            continue
        diff = score_a - score_b
        diffs.append(diff)
        if diff > 0:
            wins_a += 1
        elif diff < 0:
            wins_b += 1
        else:
            ties += 1
    total = wins_a + wins_b + ties
    if total == 0:
        return {
            "system_a": sys_a,
            "system_b": sys_b,
            "wins_a": 0,
            "ties": 0,
            "wins_b": 0,
            "win_rate_a": 0.0,
            "win_rate_b": 0.0,
            "tie_rate": 0.0,
            "mean_difference": None,
            "median_difference": None,
        }
    return {
        "system_a": sys_a,
        "system_b": sys_b,
        "wins_a": wins_a,
        "ties": ties,
        "wins_b": wins_b,
        "win_rate_a": round(wins_a / total, 3),
        "win_rate_b": round(wins_b / total, 3),
        "tie_rate": round(ties / total, 3),
        "mean_difference": round(float(np.mean(diffs)), 3),
        "median_difference": round(float(np.median(diffs)), 3),
    }


def compute_by_intent(records: list[dict]) -> list[dict]:
    by_intent: dict[str, dict[str, list[float | None]]] = defaultdict(
        lambda: {d: [] for d in DIMENSIONS}
    )
    for rec in records:
        intent = rec.get("intent", "unknown")
        for dim in DIMENSIONS:
            val = rec.get("scores", {}).get(dim)
            by_intent[intent][dim].append(val)

    results = []
    for intent in sorted(by_intent.keys()):
        entry: dict = {"intent": intent, "n_examples": len(by_intent[intent]["overall"])}
        for dim in DIMENSIONS:
            non_none = [v for v in by_intent[intent][dim] if v is not None]
            if not non_none:
                entry[f"mean_{dim}"] = None
            else:
                entry[f"mean_{dim}"] = round(float(np.mean(non_none)), 3)
        results.append(entry)
    return results


def compute_failure_tag_distribution(records: list[dict]) -> dict[str, int]:
    tag_counts: dict[str, int] = defaultdict(int)
    for rec in records:
        tags = rec.get("failure_tags", []) or []
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            tag_counts[tag] += 1
    return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare reply systems via human evaluation scores.")
    parser.add_argument("--scores", default=str(PROJECT_ROOT / "evaluation" / "data" / "human_reply_scores.jsonl"), help="Path to human_reply_scores.jsonl")
    parser.add_argument("--outdir", default=str(PROJECT_ROOT / "evaluation" / "results"), help="Output directory for results")
    args = parser.parse_args()

    scores_path = Path(args.scores)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    records = load_scores(scores_path)

    systems = sorted({r.get("system") for r in records if r.get("system")})
    if not systems:
        systems = [
            "generic_baseline",
            "historical_baseline",
            "grounded_llm",
            "grounded_llm_verified",
        ]

    all_none = True
    for rec in records:
        for dim in DIMENSIONS:
            val = rec.get("scores", {}).get(dim)
            if val is not None:
                all_none = False
                break
        if not all_none:
            break

    if not records or all_none:
        print("NO SCORES YET")
        print(f"Loaded {len(records)} record(s), no numeric scores found.")
        summary = {"status": "no_scores", "systems": systems, "n_records": len(records)}
        with open(outdir / "system_comparison_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return 0

    system_means = compute_system_means(records, systems)

    pairwise_results = []
    for sys_a, sys_b in PAIRWISE_COMPARISONS:
        pairwise_results.append(compute_pairwise(records, sys_a, sys_b))
    with open(outdir / "pairwise_comparison.json", "w", encoding="utf-8") as f:
        json.dump(pairwise_results, f, indent=2)

    by_intent = compute_by_intent(records)
    with open(outdir / "reply_quality_by_intent.json", "w", encoding="utf-8") as f:
        json.dump(by_intent, f, indent=2)

    failure_dist = compute_failure_tag_distribution(records)
    summary = {
        "system_means": system_means,
        "failure_tag_distribution": failure_dist,
        "n_records": len(records),
        "systems": systems,
    }
    with open(outdir / "system_comparison_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    header = f"{'System':<30}" + "".join(f"{d:>14}" for d in DIMENSIONS)
    print()
    print(header)
    print("-" * len(header))
    for s in systems:
        row = f"{s:<30}"
        for d in DIMENSIONS:
            val = system_means[s][d]
            if val is None:
                row += f"{'N/A':>14}"
            else:
                row += f"{val:>14.3f}"
        print(row)
    print()

    print("Pairwise overall comparisons:")
    for pw in pairwise_results:
        print(
            f"  {pw['system_a']} vs {pw['system_b']}: "
            f"A wins {pw['win_rate_a']:.1%}, B wins {pw['win_rate_b']:.1%}, "
            f"ties {pw['tie_rate']:.1%}, mean diff {pw['mean_difference']}"
        )
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

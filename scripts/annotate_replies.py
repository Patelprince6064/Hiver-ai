#!/usr/bin/env python3
"""Human annotation tool for reply quality evaluation.

Presents anonymized replies for blind human scoring.

Usage:
    python scripts/annotate_replies.py [--input evaluation/results/reply_evaluation_results.jsonl]
                                       [--output evaluation/results/human_reply_scores.jsonl]
                                       [--annotator-id annotator_1]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


DIMENSIONS = ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]

FAILURE_TAG_OPTIONS = [
    "unsupported_claim",
    "wrong_intent",
    "wrong_resolution",
    "missing_context",
    "too_generic",
    "unhelpful",
    "incomplete",
    "historical_customer_info",
    "unsupported_timeline",
    "unsupported_price",
    "unsupported_policy",
    "awkward_style",
    "too_verbose",
    "too_short",
    "retrieval_error",
    "insufficient_evidence",
    "other",
]


def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    """Get integer input within range."""
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"  Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  Please enter a valid integer.")
        except (EOFError, KeyboardInterrupt):
            print("\n\nAnnotation interrupted.")
            sys.exit(1)


def get_tags_input() -> list[str]:
    """Get failure tags from annotator."""
    print("\n  Failure tags (comma-separated numbers, or 'none'):")
    for i, tag in enumerate(FAILURE_TAG_OPTIONS, 1):
        print(f"    {i}. {tag}")

    while True:
        try:
            raw = input("  Tags: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAnnotation interrupted.")
            sys.exit(1)

        if raw.lower() in ("none", "n", ""):
            return []

        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            tags = []
            for idx in indices:
                if 0 <= idx < len(FAILURE_TAG_OPTIONS):
                    tags.append(FAILURE_TAG_OPTIONS[idx])
            return tags
        except (ValueError, IndexError):
            print("  Invalid input. Enter comma-separated numbers (e.g., '1,3,5') or 'none'.")


def get_free_text() -> str:
    """Get free-text reason from annotator."""
    try:
        return input("  Free-text reason (optional): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nAnnotation interrupted.")
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reply quality annotation tool")
    parser.add_argument(
        "--input",
        default="evaluation/results/reply_evaluation_results.jsonl",
        help="Input file with evaluation results",
    )
    parser.add_argument(
        "--output",
        default="evaluation/results/human_reply_scores.jsonl",
        help="Output file for human scores",
    )
    parser.add_argument("--annotator-id", default="annotator_1", help="Annotator identifier")
    parser.add_argument("--start", type=int, default=0, help="Start from query index")
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    output_path = PROJECT_ROOT / args.output

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        print("Run: python scripts/run_reply_evaluation.py")
        return 1

    all_records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_records.append(json.loads(line))

    queries: dict[str, list[dict]] = {}
    for rec in all_records:
        qid = rec["query_id"]
        if qid not in queries:
            queries[qid] = []
        queries[qid].append(rec)

    sorted_qids = sorted(queries.keys())
    total = len(sorted_qids)

    existing_scores = {}
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    key = (rec["query_id"], rec["system"])
                    existing_scores[key] = rec

    print("=" * 60)
    print("REPLY QUALITY ANNOTATION TOOL")
    print("=" * 60)
    print(f"\nAnnotator: {args.annotator_id}")
    print(f"Total queries: {total}")
    print(f"Replies per query: 4")
    print(f"Dimensions: {', '.join(DIMENSIONS)}")
    print(f"\nScoring: 1 (worst) to 5 (best)")
    print(f"Type 'skip' to skip a reply.")
    print(f"Type 'quit' to stop and save.\n")

    annotated = 0
    skipped = 0

    for qi, qid in enumerate(sorted_qids):
        if qi < args.start:
            continue

        replies = queries[qid]
        customer_msg = replies[0]["customer_message"]
        intent = replies[0].get("intent", "")

        print(f"\n{'─' * 60}")
        print(f"Query {qi + 1}/{total} [{qid}]")
        print(f"Intent: {intent}")
        print(f"\nCustomer: {customer_msg[:200]}{'...' if len(customer_msg) > 200 else ''}")

        for reply_rec in replies:
            blind_label = reply_rec["system"]
            reply_text = reply_rec.get("reply", "") or "(no reply)"

            print(f"\n  ┌─ {blind_label} ─")
            print(f"  │ {reply_text[:300]}{'...' if len(reply_text) > 300 else ''}")
            print(f"  └─")

            key = (reply_rec["query_id"], blind_label)
            if key in existing_scores and existing_scores[key].get("scores", {}).get("overall") is not None:
                print(f"  [Already annotated. Scores: {existing_scores[key]['scores']}]")
                try:
                    redo = input("  Redo? (y/n): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\n\nAnnotation interrupted.")
                    break
                if redo != "y":
                    skipped += 1
                    continue

            scores = {}
            for dim in DIMENSIONS:
                score = get_int_input(f"  {dim.capitalize()} (1-5): ", 1, 5)
                scores[dim] = score

            valid_scores = [v for v in scores.values() if v is not None]
            scores["overall"] = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None

            tags = get_tags_input()
            reason = get_free_text()

            score_record = {
                "query_id": reply_rec["query_id"],
                "conversation_id": reply_rec.get("conversation_id", ""),
                "message_id": reply_rec.get("message_id", ""),
                "customer_message": customer_msg,
                "intent": intent,
                "split": reply_rec.get("split", "dev"),
                "system": blind_label,
                "system_name": reply_rec.get("system_name", ""),
                "reply": reply_rec.get("reply", ""),
                "retrieval_status": reply_rec.get("retrieval_status", ""),
                "evidence_ids": reply_rec.get("evidence_ids", []),
                "grounding_status": reply_rec.get("grounding_status", ""),
                "grounding_score": reply_rec.get("grounding_score"),
                "scores": scores,
                "failure_tags": tags,
                "free_text_reason": reason,
                "annotator_id": args.annotator_id,
                "metadata": {},
            }

            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(score_record, ensure_ascii=False) + "\n")

            annotated += 1

        try:
            cont = input("\n  Continue to next query? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAnnotation session ended.")
            break
        if cont == "n":
            break

    print(f"\n{'=' * 60}")
    print("ANNOTATION SESSION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Annotated: {annotated}")
    print(f"Skipped: {skipped}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

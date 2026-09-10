"""Batch processing for the end-to-end agent.

Run the support agent on a JSONL input file.

Usage:
    python scripts/run_agent_batch.py --input data/interim/agent_eval/requests.jsonl --output evaluation/results/agent_outputs.jsonl
"""

import argparse
import json
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import create_agent


def process_batch(
    input_path: Path,
    output_path: Path,
    mock_mode: bool = False,
) -> dict:
    """Process a batch of requests.

    Args:
        input_path: Path to JSONL input file.
        output_path: Path to JSONL output file.
        mock_mode: If True, use mock mode.

    Returns:
        Summary statistics.
    """
    agent = create_agent(mock_mode=mock_mode)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    success = 0
    auto_handle = 0
    escalate = 0
    errors = 0
    start_time = time.time()

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue

            total += 1

            try:
                request_data = json.loads(line)
                request = AgentRequest(
                    message=request_data.get("message", ""),
                    conversation_id=request_data.get("conversation_id"),
                    message_id=request_data.get("message_id"),
                    conversation_context=request_data.get("conversation_context", []),
                )

                response = agent.process(request)

                response_dict = {
                    "decision": response.decision,
                    "reply": response.reply,
                    "intent": response.intent,
                    "intent_confidence": response.intent_confidence,
                    "grounding_status": response.grounding_status,
                    "escalation": {
                        "decision": response.escalation.decision,
                        "reason_codes": response.escalation.reason_codes,
                        "risk_level": response.escalation.risk_level,
                        "policy_version": response.escalation.policy_version,
                    },
                    "trace_id": response.trace_id,
                    "input_message": request.message[:100],
                }

                fout.write(json.dumps(response_dict, ensure_ascii=False) + "\n")

                success += 1
                if response.decision == "AUTO_HANDLE":
                    auto_handle += 1
                else:
                    escalate += 1

            except Exception as e:
                errors += 1
                error_response = {
                    "decision": "SYSTEM_FAILURE",
                    "error": str(e),
                    "input_message": line[:100] if line else "",
                }
                fout.write(json.dumps(error_response, ensure_ascii=False) + "\n")
                print(f"Error processing line {line_num}: {e}", file=sys.stderr)

    elapsed = time.time() - start_time

    summary = {
        "total": total,
        "success": success,
        "auto_handle": auto_handle,
        "escalate": escalate,
        "errors": errors,
        "auto_handle_rate": auto_handle / total if total > 0 else 0.0,
        "escalate_rate": escalate / total if total > 0 else 0.0,
        "error_rate": errors / total if total > 0 else 0.0,
        "elapsed_seconds": elapsed,
        "requests_per_second": total / elapsed if elapsed > 0 else 0.0,
    }

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch process customer messages through the support agent"
    )
    parser.add_argument(
        "--input", required=True, help="Input JSONL file path"
    )
    parser.add_argument(
        "--output", required=True, help="Output JSONL file path"
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock mode (no API keys required)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    summary = process_batch(input_path, output_path, mock_mode=args.mock)

    print("\n=== Batch Processing Summary ===")
    print(f"Total requests: {summary['total']}")
    print(f"Successful: {summary['success']}")
    print(f"AUTO_HANDLE: {summary['auto_handle']} ({summary['auto_handle_rate']:.1%})")
    print(f"ESCALATE: {summary['escalate']} ({summary['escalate_rate']:.1%})")
    print(f"Errors: {summary['errors']} ({summary['error_rate']:.1%})")
    print(f"Elapsed: {summary['elapsed_seconds']:.2f}s")
    print(f"Throughput: {summary['requests_per_second']:.2f} req/s")
    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()

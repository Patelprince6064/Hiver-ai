"""End-to-end agent CLI.

Run the support agent on a single customer message.

Usage:
    python scripts/run_agent.py --message "Where is my order?"
    python scripts/run_agent.py --message "test" --mock
"""

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import create_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the end-to-end support agent"
    )
    parser.add_argument(
        "--message", required=True, help="Customer message to process"
    )
    parser.add_argument(
        "--conversation-id", default=None, help="Optional conversation ID"
    )
    parser.add_argument(
        "--message-id", default=None, help="Optional message ID"
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock mode (no API keys required)"
    )
    parser.add_argument(
        "--output", default=None, help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    request = AgentRequest(
        message=args.message,
        conversation_id=args.conversation_id,
        message_id=args.message_id,
    )

    agent = create_agent(mock_mode=args.mock)
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
            "recommended_action": response.escalation.recommended_action,
        },
        "trace_id": response.trace_id,
    }

    if response.human_review:
        response_dict["human_review"] = {
            "customer_message": response.human_review.customer_message,
            "predicted_intent": response.human_review.predicted_intent,
            "intent_confidence": response.human_review.intent_confidence,
            "escalation_reasons": response.human_review.escalation_reasons,
            "recommended_action": response.human_review.recommended_action,
            "draft_reply": response.human_review.draft_reply,
        }

    output_json = json.dumps(response_dict, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
        print(f"Output written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()

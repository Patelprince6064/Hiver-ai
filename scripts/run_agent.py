"""End-to-end agent CLI and interactive demonstration.

Run the support agent on customer messages or execute representative demo scenarios.

Usage:
    python scripts/run_agent.py --demo
    python scripts/run_agent.py --message "Where is my order?" --mock
    python scripts/run_agent.py --message "I want to delete my account" --demo
"""

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import SupportAgent, create_agent
from src.generation.reply_schema import build_reply_output, ReplyOutput
from src.retrieval.retrieval_schema import RetrievalResponse, RetrievalResult


class DemoMockClassifier:
    """Mock intent classifier reflecting query difficulty and semantic ambiguity."""
    def predict_with_confidence(self, texts: list[str]) -> list[dict]:
        results = []
        for t in texts:
            tl = t.lower()
            if any(w in tl for w in ["delete", "cancel", "refund", "lawsuit", "dispute"]):
                results.append({
                    "intent": "account_help",
                    "confidence": 0.88,
                    "probabilities": {"account_help": 0.88, "refund": 0.12},
                })
            elif any(w in tl for w in ["setup", "broken", "weird", "maybe", "confused"]) or len(t.split()) < 6:
                results.append({
                    "intent": "general_inquiry",
                    "confidence": 0.42,
                    "probabilities": {"general_inquiry": 0.42, "product_question": 0.38},
                })
            else:
                results.append({
                    "intent": "order_status",
                    "confidence": 0.86,
                    "probabilities": {"order_status": 0.86, "shipping": 0.14},
                })
        return results


class DemoMockRetriever:
    """Mock knowledge base retriever reflecting evidence availability."""
    def retrieve(self, query: str, top_k: int = 5, intent: str = None, **kwargs) -> RetrievalResponse:
        ql = query.lower()
        if any(w in ql for w in ["setup", "broken", "maybe"]) or len(query.split()) < 6:
            return RetrievalResponse(
                query=query,
                retrieval_status="empty",
                results=[],
            )
        elif any(w in ql for w in ["delete", "cancel", "refund"]):
            return RetrievalResponse(
                query=query,
                retrieval_status="success",
                results=[
                    RetrievalResult(
                        rank=1,
                        knowledge_id="KB_AUTH_001",
                        customer_message=query,
                        support_response="Account cancellations and refund requests require supervisor verification.",
                        similarity_score=0.91,
                        intent="account_help",
                        conversation_id="conv_auth_01",
                        source_message_id="msg_auth_01",
                        resolution_type="escalation",
                    )
                ],
            )
        else:
            return RetrievalResponse(
                query=query,
                retrieval_status="success",
                results=[
                    RetrievalResult(
                        rank=1,
                        knowledge_id="KB_ORD_001",
                        customer_message=query,
                        support_response="Your order has shipped and tracking information typically updates within 24 to 48 hours.",
                        similarity_score=0.88,
                        intent="order_status",
                        conversation_id="conv_ord_01",
                        source_message_id="msg_ord_01",
                        resolution_type="direct",
                    )
                ],
            )


class DemoMockGenerator:
    """Mock grounded generator reflecting constrained response generation."""
    def generate(self, customer_message: str = "", predicted_intent: str = "", intent_confidence: float = 0.8, evidence: list = None, **kwargs) -> ReplyOutput:
        ql = customer_message.lower()
        if any(w in ql for w in ["delete", "cancel", "refund"]):
            return build_reply_output(
                query=customer_message,
                reply="Account cancellations and refund requests require supervisor verification.",
                generation_method="grounded_llm",
                status="success",
                predicted_intent=predicted_intent or "account_help",
                intent_confidence=intent_confidence or 0.88,
                evidence=evidence or [],
                risk_flags=["high_risk_action"],
            )
        elif any(w in ql for w in ["setup", "broken", "maybe"]) or len(customer_message.split()) < 6:
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="fallback_macro",
                status="insufficient_evidence",
                predicted_intent=predicted_intent or "general_inquiry",
                intent_confidence=intent_confidence or 0.42,
                evidence=[],
            )
        else:
            return build_reply_output(
                query=customer_message,
                reply="Your order has shipped and tracking information typically updates within 24 to 48 hours.",
                generation_method="grounded_llm",
                status="success",
                predicted_intent=predicted_intent or "order_status",
                intent_confidence=intent_confidence or 0.86,
                evidence=evidence or [],
            )


def build_demo_agent(mock_mode: bool = True) -> SupportAgent:
    """Instantiate agent wired with realistic component pipelines for demonstration."""
    if mock_mode:
        return SupportAgent(
            classifier=DemoMockClassifier(),
            retriever=DemoMockRetriever(),
            generator=DemoMockGenerator(),
            mock_mode=False,  # Use specialized demo components through standard pipeline
        )
    return create_agent(mock_mode=False)


def print_demo_card(message: str, response, evidence_summary: str = "Standard policy passages matching customer intent.") -> None:
    """Format and print structured agent decision without hidden chain-of-thought."""
    grounding = (response.grounding_status or "PASS").upper()
    evidence_status = "SUFFICIENT" if response.grounding_status != "fail" and response.intent_confidence >= 0.50 else "INSUFFICIENT"
    
    if response.decision == "ESCALATE_TO_HUMAN":
        reason = ", ".join(response.escalation.reason_codes) if response.escalation.reason_codes else "Escalation policy threshold triggered"
    else:
        reason = "Confidence and verification thresholds satisfied for safe auto-handling."

    reply_text = response.reply or (response.human_review.draft_reply if response.human_review else "Draft escalated to human specialist.")

    print("==================================================")
    print("AI SUPPORT AGENT DEMO")
    print("==================================================")
    print(f"Customer:\n{message}\n")
    print(f"Intent:\n{response.intent}\n")
    print(f"Intent Confidence:\n{response.intent_confidence:.3f}\n")
    print(f"Retrieved Evidence:\n{evidence_summary}\n")
    print(f"Evidence Status:\n{evidence_status}\n")
    print(f"Draft Reply:\n{reply_text}\n")
    print(f"Grounding:\n{grounding}\n")
    print(f"Final Decision:\n{response.decision}\n")
    print(f"Reason:\n{reason}")
    print("==================================================\n")


def run_demo_scenarios(agent: SupportAgent) -> None:
    """Run three representative customer support scenarios illustrating routing behavior."""
    demo_cases = [
        {
            "desc": "Scenario 1: Routine inquiry with clear intent and high grounding (Safe Auto-Handle)",
            "message": "Where is my order #12345? Tracking shows it shipped 2 days ago.",
            "evidence": "Historical support passage: Orders ship within 1-2 business days and tracking details update via email.",
        },
        {
            "desc": "Scenario 2: Ambiguous / Low-confidence inquiry (Safe Human Escalation)",
            "message": "Can you help me with my setup?",
            "evidence": "Zero relevant knowledge base passages found above similarity threshold (0.30).",
        },
        {
            "desc": "Scenario 3: Safety-critical high-risk action request (Mandatory Human Escalation)",
            "message": "I want to delete my account and demand a full refund immediately.",
            "evidence": "Historical support passage: Account cancellations and refund requests require supervisor verification.",
        },
    ]

    print("\n" + "#" * 60)
    print("RUNNING HIVER AI SUPPORT AGENT — DEMONSTRATION SUITE")
    print("#" * 60 + "\n")

    for case in demo_cases:
        print(f"--- {case['desc']} ---")
        req = AgentRequest(message=case["message"])
        res = agent.process(req)
        print_demo_card(case["message"], res, case["evidence"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the end-to-end support agent or demo")
    parser.add_argument(
        "--message", default=None, help="Customer message to process"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run formatted demo output"
    )
    parser.add_argument(
        "--conversation-id", default=None, help="Optional conversation ID"
    )
    parser.add_argument(
        "--message-id", default=None, help="Optional message ID"
    )
    parser.add_argument(
        "--live", action="store_true", help="Use live models rather than lightweight mock components"
    )
    parser.add_argument(
        "--output", default=None, help="Output file path (default: stdout)"
    )

    args = parser.parse_args()
    agent = build_demo_agent(mock_mode=not args.live)

    if args.demo and not args.message:
        run_demo_scenarios(agent)
        return

    if not args.message:
        print("Error: Either --demo or --message is required.")
        parser.print_help()
        sys.exit(1)

    request = AgentRequest(
        message=args.message,
        conversation_id=args.conversation_id,
        message_id=args.message_id,
    )

    response = agent.process(request)

    if args.demo:
        print_demo_card(args.message, response)
        return

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

"""Reply repair strategy.

When grounding verification fails, attempts to repair the reply
by removing unsupported claims.
"""

from typing import Any

from src.generation.llm.base_provider import BaseLLMProvider, LLMResponse
from src.generation.reply_schema import ReplyOutput, build_reply_output


REPAIR_PROMPT_TEMPLATE = """You are a customer-support reply editor.

The original reply contained unsupported claims that must be removed or rewritten.

CURRENT CUSTOMER MESSAGE:
{customer_message}

VALID HISTORICAL EVIDENCE:
{evidence}

ORIGINAL REPLY:
{original_reply}

DETECTED UNSUPPORTED CLAIMS:
{unsupported_claims}

INSTRUCTIONS:
1. Remove or rewrite the unsupported claims listed above.
2. Do NOT introduce new facts, policies, timelines, prices, or guarantees.
3. Use ONLY information present in the supplied evidence.
4. If a safe reply cannot be produced, respond with ONLY: INSUFFICIENT_EVIDENCE
5. Keep the reply concise, polite, and actionable.
6. Do not mention that you are an AI or reference internal systems.

REPAIRED REPLY:"""


class ReplyRepairer:
    """Repairs replies that fail grounding verification."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        max_attempts: int = 1,
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> None:
        self.llm_provider = llm_provider
        self.max_attempts = max_attempts
        self.temperature = temperature
        self.max_tokens = max_tokens

    def repair(
        self,
        customer_message: str,
        original_reply: str,
        evidence: list[dict[str, Any]],
        unsupported_claims: list[dict[str, Any]],
    ) -> ReplyOutput:
        """Attempt to repair a reply by removing unsupported claims.

        Args:
            customer_message: The original customer message.
            original_reply: The reply that failed verification.
            evidence: The evidence used.
            unsupported_claims: The claims that were unsupported.

        Returns:
            ReplyOutput with repaired reply or failure status.
        """
        evidence_text = _format_evidence(evidence)
        claims_text = _format_unsupported_claims(unsupported_claims)

        prompt = REPAIR_PROMPT_TEMPLATE.format(
            customer_message=customer_message,
            evidence=evidence_text,
            original_reply=original_reply,
            unsupported_claims=claims_text,
        )

        llm_response: LLMResponse = self.llm_provider.generate(
            prompt=prompt,
            system_prompt="You are a careful customer-support reply editor. Edit only what is necessary.",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if llm_response.status != "success":
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm_repair",
                status="provider_error",
                evidence=evidence,
                metadata={
                    "error_type": llm_response.error_type,
                    "error_message": llm_response.error_message,
                    "repair_attempt": True,
                },
            )

        repaired_text = llm_response.text.strip()

        if not repaired_text or repaired_text.upper() == "INSUFFICIENT_EVIDENCE":
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm_repair",
                status="insufficient_evidence",
                evidence=evidence,
                metadata={
                    "repair_attempt": True,
                    "repair_result": "insufficient_evidence",
                },
            )

        return build_reply_output(
            query=customer_message,
            reply=repaired_text,
            generation_method="grounded_llm_repair",
            status="success",
            evidence=evidence,
            metadata={
                "repair_attempt": True,
                "original_reply": original_reply,
                "n_unsupported_claims": len(unsupported_claims),
            },
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "repairer": "ReplyRepairer",
            "llm_provider": self.llm_provider.get_params(),
            "max_attempts": self.max_attempts,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


def _format_evidence(evidence: list[dict[str, Any]]) -> str:
    """Format evidence for the repair prompt."""
    parts = []
    for i, ev in enumerate(evidence, 1):
        parts.append(
            f"[{i}] Customer: {ev.get('customer_message', 'N/A')}\n"
            f"    Support: {ev.get('support_response', 'N/A')}"
        )
    return "\n".join(parts) if parts else "No evidence available."


def _format_unsupported_claims(unsupported_claims: list[dict[str, Any]]) -> str:
    """Format unsupported claims for the repair prompt."""
    parts = []
    for i, claim in enumerate(unsupported_claims, 1):
        parts.append(
            f"{i}. \"{claim.get('claim', '')}\" (type: {claim.get('type', 'unknown')})"
        )
    return "\n".join(parts) if parts else "None detected."

"""Generic reply baseline.

Returns a static generic support response.
"""

from typing import Any

from src.generation.base_generator import BaseReplyGenerator
from src.generation.reply_schema import ReplyOutput, build_reply_output

GENERIC_REPLY = "Thanks for reaching out. We're sorry you're experiencing this issue. Please provide more details so our support team can assist you."


class GenericReplyGenerator(BaseReplyGenerator):
    """Generic baseline: returns a fixed support response."""

    def __init__(self, fallback_reply: str | None = None) -> None:
        self.fallback_reply = fallback_reply or GENERIC_REPLY

    def generate(
        self,
        customer_message: str,
        context: list[dict[str, Any]] | None = None,
        intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> ReplyOutput:
        return build_reply_output(
            query=customer_message,
            reply=self.fallback_reply,
            generation_method="generic_baseline",
            status="success",
            predicted_intent=intent,
            intent_confidence=intent_confidence,
            evidence=[],
            risk_flags=[],
            metadata={"is_generic": True},
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "generator": "GenericReplyGenerator",
            "fallback_reply": self.fallback_reply,
        }

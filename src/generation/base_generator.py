"""Base reply generator interface.

Defines the common interface for all reply generators.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.generation.reply_schema import ReplyOutput


class BaseReplyGenerator(ABC):
    """Abstract base class for reply generators."""

    @abstractmethod
    def generate(
        self,
        customer_message: str,
        context: list[dict[str, Any]] | None = None,
        intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> ReplyOutput:
        """Generate a reply for a customer message.

        Args:
            customer_message: The customer's message.
            context: Optional conversation context (list of prior messages).
            intent: Optional pre-classified intent.
            intent_confidence: Optional intent confidence score.

        Returns:
            ReplyOutput with the generated reply.
        """
        ...

    def get_params(self) -> dict[str, Any]:
        """Return generator parameters."""
        return {"generator": self.__class__.__name__}

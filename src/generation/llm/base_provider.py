"""Base LLM provider interface.

Defines the common interface for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    text: str = ""
    status: str = "success"  # success | provider_error | timeout | rate_limit
    error_type: str | None = None
    error_message: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    model: str = ""


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 300,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with generated text or error.
        """
        ...

    def get_params(self) -> dict[str, Any]:
        """Return provider parameters."""
        return {"provider": self.__class__.__name__}

"""Mock LLM provider for testing and development.

Returns deterministic responses without API calls.
"""

import time
from typing import Any

from src.generation.llm.base_provider import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Mock provider that returns predefined responses."""

    def __init__(
        self,
        response: str = "Mock grounded response.",
        status: str = "success",
        latency_ms: float = 50.0,
        usage: dict[str, Any] | None = None,
    ) -> None:
        self.response = response
        self.status = status
        self.latency_ms = latency_ms
        self.usage = usage or {
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
        }
        self._call_count = 0
        self._last_prompt: str = ""
        self._last_system_prompt: str | None = None

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 300,
        **kwargs: Any,
    ) -> LLMResponse:
        self._call_count += 1
        self._last_prompt = prompt
        self._last_system_prompt = system_prompt

        return LLMResponse(
            text=self.response,
            status=self.status,
            usage=self.usage,
            latency_ms=self.latency_ms,
            model="mock-model",
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "provider": "MockLLMProvider",
            "response": self.response,
            "status": self.status,
            "call_count": self._call_count,
        }

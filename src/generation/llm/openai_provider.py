"""OpenAI LLM provider.

Uses the OpenAI API for text generation.
"""

import json
import os
import time
from typing import Any

from src.generation.llm.base_provider import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 1,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Set the environment variable or pass api_key."
                )
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 300,
        **kwargs: Any,
    ) -> LLMResponse:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                text = response.choices[0].message.content or ""
                latency_ms = (time.time() - start_time) * 1000

                usage = {}
                if response.usage:
                    usage = {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }

                return LLMResponse(
                    text=text.strip(),
                    status="success",
                    usage=usage,
                    latency_ms=latency_ms,
                    model=self.model,
                )

            except Exception as e:
                last_error = e
                error_type = type(e).__name__.lower()
                if "rate" in str(e).lower():
                    error_type = "rate_limit"
                elif "timeout" in str(e).lower():
                    error_type = "timeout"
                elif "api" in str(e).lower() or "auth" in str(e).lower():
                    error_type = "api_error"

                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue

                latency_ms = (time.time() - start_time) * 1000
                return LLMResponse(
                    text="",
                    status="provider_error",
                    error_type=error_type,
                    error_message=str(e),
                    usage={},
                    latency_ms=latency_ms,
                    model=self.model,
                )

        latency_ms = (time.time() - start_time) * 1000
        return LLMResponse(
            text="",
            status="provider_error",
            error_type="unknown",
            error_message=str(last_error),
            usage={},
            latency_ms=latency_ms,
            model=self.model,
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "provider": "OpenAIProvider",
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

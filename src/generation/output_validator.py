"""Output validator for LLM-generated replies.

Validates that generated replies meet quality and safety requirements.
"""

import re
from dataclasses import dataclass, field
from typing import Any


INTERNAL_TERMS = {
    "faiss", "retriever", "embedding", "llm", "system prompt",
    "knowledge base", "index", "vector", "cosine similarity",
    "prompt injection", "ignore previous instructions",
}


@dataclass
class ValidationResult:
    """Result of output validation."""

    is_valid: bool
    status: str  # success | invalid_output
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class OutputValidator:
    """Validates LLM-generated reply output."""

    def __init__(
        self,
        max_reply_length: int = 500,
        min_reply_length: int = 5,
    ) -> None:
        self.max_reply_length = max_reply_length
        self.min_reply_length = min_reply_length

    def validate(
        self,
        raw_output: str,
        evidence_ids: list[str] | None = None,
        customer_message: str = "",
    ) -> ValidationResult:
        """Validate raw LLM output.

        Args:
            raw_output: The raw text from the LLM.
            evidence_ids: Valid evidence IDs that were supplied.
            customer_message: The original customer message.

        Returns:
            ValidationResult with validity status and errors.
        """
        errors = []
        warnings = []

        text = raw_output.strip()

        if not text:
            return ValidationResult(
                is_valid=False,
                status="invalid_output",
                errors=["Empty output"],
            )

        if text.upper() == "INSUFFICIENT_EVIDENCE":
            return ValidationResult(
                is_valid=True,
                status="insufficient_evidence",
            )

        if len(text) > self.max_reply_length:
            errors.append(
                f"Reply too long ({len(text)} chars > {self.max_reply_length})"
            )

        if len(text.split()) < self.min_reply_length // 5:
            warnings.append("Reply is very short")

        text_lower = text.lower()
        for term in INTERNAL_TERMS:
            if term in text_lower:
                warnings.append(f"Contains internal term: {term}")

        if customer_message:
            customer_tokens = set(customer_message.lower().split())
            reply_tokens = set(text_lower.split())
            overlap = customer_tokens & reply_tokens
            if len(overlap) < 2 and len(customer_tokens) > 3:
                warnings.append("Low token overlap with customer message")

        return ValidationResult(
            is_valid=len(errors) == 0,
            status="success" if len(errors) == 0 else "invalid_output",
            errors=errors,
            warnings=warnings,
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "max_reply_length": self.max_reply_length,
            "min_reply_length": self.min_reply_length,
        }

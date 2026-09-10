"""Context budget management for LLM prompts.

Limits the total size of evidence and context sent to the LLM.
"""

from typing import Any


DEFAULT_MAX_CUSTOMER_MESSAGE_CHARS = 500
DEFAULT_MAX_EVIDENCE_ITEM_CHARS = 300
DEFAULT_MAX_TOTAL_EVIDENCE_CHARS = 1500


class ContextBudget:
    """Manages context size limits for LLM prompts."""

    def __init__(
        self,
        max_customer_message_chars: int = DEFAULT_MAX_CUSTOMER_MESSAGE_CHARS,
        max_evidence_item_chars: int = DEFAULT_MAX_EVIDENCE_ITEM_CHARS,
        max_total_evidence_chars: int = DEFAULT_MAX_TOTAL_EVIDENCE_CHARS,
    ) -> None:
        self.max_customer_message_chars = max_customer_message_chars
        self.max_evidence_item_chars = max_evidence_item_chars
        self.max_total_evidence_chars = max_total_evidence_chars

    def fit_customer_message(self, message: str) -> str:
        """Truncate customer message if too long."""
        if len(message) <= self.max_customer_message_chars:
            return message
        return message[: self.max_customer_message_chars] + "..."

    def fit_evidence(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fit evidence items within the total budget."""
        fitted = []
        total_chars = 0

        for item in evidence:
            response = item.get("support_response", "")
            if len(response) > self.max_evidence_item_chars:
                response = response[: self.max_evidence_item_chars] + "..."
                item = {**item, "support_response": response}

            customer_msg = item.get("customer_message", "")
            if len(customer_msg) > self.max_evidence_item_chars:
                customer_msg = customer_msg[: self.max_evidence_item_chars] + "..."
                item = {**item, "customer_message": customer_msg}

            item_chars = len(response) + len(customer_msg)
            if total_chars + item_chars > self.max_total_evidence_chars:
                break

            total_chars += item_chars
            fitted.append(item)

        return fitted

    def get_params(self) -> dict[str, Any]:
        return {
            "max_customer_message_chars": self.max_customer_message_chars,
            "max_evidence_item_chars": self.max_evidence_item_chars,
            "max_total_evidence_chars": self.max_total_evidence_chars,
        }

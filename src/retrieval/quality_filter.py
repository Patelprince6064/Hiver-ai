"""Quality filtering for knowledge base records.

Applies quality flags and categories to knowledge base records.
"""

import re
from typing import Any


# Quality flag definitions
QUALITY_FLAGS = {
    "empty_customer_message": "Customer message is empty or whitespace-only",
    "empty_support_response": "Support response is empty or whitespace-only",
    "very_short_message": "Customer message has fewer than 3 words",
    "duplicate": "Exact duplicate customer-support pair",
    "missing_conversation_id": "No conversation ID available",
    "uncertain_pairing": "Customer-support pairing may be incorrect",
    "unclear_resolution": "Resolution type could not be determined",
    "multi_turn_context": "Multiple customer messages in conversation",
    "high_noise": "Message contains excessive URLs, mentions, or hashtags",
    "possible_language_mismatch": "Possible non-English content",
}


def apply_quality_flags(record: dict[str, Any]) -> list[str]:
    """Apply quality flags to a knowledge record."""
    flags = []

    customer_msg = record.get("customer_message", "")
    support_resp = record.get("support_response", "")

    # Empty messages
    if not customer_msg or not customer_msg.strip():
        flags.append("empty_customer_message")
    if not support_resp or not support_resp.strip():
        flags.append("empty_support_response")

    # Very short messages
    if customer_msg and len(customer_msg.split()) < 3:
        flags.append("very_short_message")

    # Missing conversation ID
    if not record.get("conversation_id"):
        flags.append("missing_conversation_id")

    # Unclear resolution
    if record.get("resolution_type") in ["unclear", "no_resolution", "other"]:
        flags.append("unclear_resolution")

    # High noise
    noise_count = 0
    if re.search(r"https?://\S+", customer_msg):
        noise_count += 1
    if re.search(r"@\w+", customer_msg):
        noise_count += 1
    if re.search(r"#\w+", customer_msg):
        noise_count += 1
    if noise_count >= 2:
        flags.append("high_noise")

    return flags


def categorize_quality(flags: list[str]) -> str:
    """Categorize record quality based on flags."""
    if not flags:
        return "usable"

    severe_flags = {"empty_customer_message", "empty_support_response", "missing_conversation_id"}
    if severe_flags & set(flags):
        return "low_quality"

    mild_flags = {"very_short_message", "unclear_resolution", "high_noise"}
    if mild_flags & set(flags):
        return "usable_with_context"

    return "usable"


def detect_duplicates(records: list[dict[str, Any]]) -> dict[str, int]:
    """Detect exact duplicate customer-support pairs."""
    seen = {}
    for record in records:
        key = (
            record.get("customer_message", "").strip().lower(),
            record.get("support_response", "").strip().lower(),
        )
        if key in seen:
            seen[key] += 1
        else:
            seen[key] = 1
    return seen

"""Conversation complexity signal extraction.

Uses available conversation information to estimate complexity
for escalation decisions. Heuristic-based, not ML-based.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationComplexity:
    """Container for conversation complexity signals."""

    num_turns: int = 0
    num_customer_messages: int = 0
    num_support_responses: int = 0
    avg_message_length: float = 0.0
    has_repeated_request: bool = False
    has_multiple_intents: bool = False
    has_contradictory_requests: bool = False
    has_unresolved_prior_turns: bool = False
    complexity_score: float = 0.0
    complexity_level: str = "low"  # low, medium, high


def compute_conversation_complexity(
    conversation_history: list[dict[str, str]] | None = None,
    current_message: str = "",
    detected_intents: list[str] | None = None,
    previous_responses: list[str] | None = None,
) -> ConversationComplexity:
    """Compute conversation complexity signals.

    Args:
        conversation_history: List of message dicts with 'role' and 'text'.
        current_message: The current customer message.
        detected_intents: List of detected intents if available.
        previous_responses: List of previous support responses.

    Returns:
        ConversationComplexity with extracted signals.
    """
    complexity = ConversationComplexity()

    if not conversation_history:
        # No conversation history — minimal complexity
        complexity.num_turns = 0
        complexity.num_customer_messages = 1
        complexity.avg_message_length = len(current_message) if current_message else 0
        complexity.complexity_score = 0.1
        complexity.complexity_level = "low"
        return complexity

    # Count turns and messages
    customer_messages = []
    support_responses = []

    for turn in conversation_history:
        role = turn.get("role", "").lower()
        text = turn.get("text", "")
        if role in ("customer", "user", "human"):
            customer_messages.append(text)
        elif role in ("support", "agent", "assistant", "system"):
            support_responses.append(text)

    complexity.num_turns = len(conversation_history)
    complexity.num_customer_messages = len(customer_messages)
    complexity.num_support_responses = len(support_responses)

    # Average message length
    all_texts = [t.get("text", "") for t in conversation_history]
    if all_texts:
        complexity.avg_message_length = sum(len(t) for t in all_texts) / len(all_texts)

    # Detect repeated requests
    if len(customer_messages) >= 2:
        unique_messages = set(m.strip().lower() for m in customer_messages if m.strip())
        if len(unique_messages) < len(customer_messages) * 0.7:
            complexity.has_repeated_request = True

    # Detect multiple intents
    if detected_intents and len(detected_intents) > 1:
        complexity.has_multiple_intents = True

    # Detect contradictory requests (simple heuristic)
    contradictory_pairs = [
        ("cancel", "keep"),
        ("refund", "exchange"),
        ("delete", "restore"),
        ("close", "open"),
        ("stop", "start"),
    ]
    all_text = " ".join(m.lower() for m in customer_messages)
    for word1, word2 in contradictory_pairs:
        if word1 in all_text and word2 in all_text:
            complexity.has_contradictory_requests = True
            break

    # Detect unresolved prior turns (heuristic: multiple support responses)
    if len(support_responses) >= 2:
        # If there are multiple support responses, the issue may not be resolved
        complexity.has_unresolved_prior_turns = True

    # Compute complexity score (0.0 to 1.0)
    score = 0.0

    # Number of turns contribution (0-0.3)
    score += min(complexity.num_turns / 10.0, 0.3)

    # Repeated request contribution (0-0.2)
    if complexity.has_repeated_request:
        score += 0.2

    # Multiple intents contribution (0-0.15)
    if complexity.has_multiple_intents:
        score += 0.15

    # Contradictory requests contribution (0-0.2)
    if complexity.has_contradictory_requests:
        score += 0.2

    # Unresolved prior turns contribution (0-0.15)
    if complexity.has_unresolved_prior_turns:
        score += 0.15

    # Long messages contribution (0-0.1)
    if complexity.avg_message_length > 200:
        score += 0.1

    complexity.complexity_score = min(score, 1.0)

    # Classify complexity level
    if complexity.complexity_score < 0.3:
        complexity.complexity_level = "low"
    elif complexity.complexity_score < 0.6:
        complexity.complexity_level = "medium"
    else:
        complexity.complexity_level = "high"

    return complexity


def complexity_to_dict(complexity: ConversationComplexity) -> dict[str, Any]:
    """Convert ConversationComplexity to a plain dict for serialization."""
    return {
        "num_turns": complexity.num_turns,
        "num_customer_messages": complexity.num_customer_messages,
        "num_support_responses": complexity.num_support_responses,
        "avg_message_length": complexity.avg_message_length,
        "has_repeated_request": complexity.has_repeated_request,
        "has_multiple_intents": complexity.has_multiple_intents,
        "has_contradictory_requests": complexity.has_contradictory_requests,
        "has_unresolved_prior_turns": complexity.has_unresolved_prior_turns,
        "complexity_score": complexity.complexity_score,
        "complexity_level": complexity.complexity_level,
    }

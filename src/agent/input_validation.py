"""Input validation for agent requests.

Validates incoming customer messages and optional fields.
"""

from typing import Any

from src.agent.agent_schema import AgentRequest


class ValidationError:
    """Validation error details."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "message": self.message}


class ValidationResult:
    """Result of input validation."""

    def __init__(self) -> None:
        self.is_valid = True
        self.errors: list[ValidationError] = []

    def add_error(self, field: str, message: str) -> None:
        self.is_valid = False
        self.errors.append(ValidationError(field, message))

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
        }


MAX_MESSAGE_LENGTH = 10000
MAX_CONTEXT_LENGTH = 50


def validate_request(request: AgentRequest) -> ValidationResult:
    """Validate an agent request.

    Args:
        request: The agent request to validate.

    Returns:
        ValidationResult with is_valid flag and any errors.
    """
    result = ValidationResult()

    if not request.message:
        result.add_error("message", "Message is required")
        return result

    if not isinstance(request.message, str):
        result.add_error("message", "Message must be a string")
        return result

    message = request.message.strip()
    if not message:
        result.add_error("message", "Message cannot be empty")
        return result

    if len(message) > MAX_MESSAGE_LENGTH:
        result.add_error(
            "message",
            f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters",
        )

    if request.conversation_id is not None and not isinstance(request.conversation_id, str):
        result.add_error("conversation_id", "conversation_id must be a string")

    if request.message_id is not None and not isinstance(request.message_id, str):
        result.add_error("message_id", "message_id must be a string")

    if request.conversation_context:
        if not isinstance(request.conversation_context, list):
            result.add_error(
                "conversation_context", "conversation_context must be a list"
            )
        elif len(request.conversation_context) > MAX_CONTEXT_LENGTH:
            result.add_error(
                "conversation_context",
                f"conversation_context exceeds maximum length of {MAX_CONTEXT_LENGTH}",
            )

    return result


def validate_message(message: Any) -> ValidationResult:
    """Validate a raw message (before creating AgentRequest).

    Args:
        message: The raw message to validate.

    Returns:
        ValidationResult with is_valid flag and any errors.
    """
    result = ValidationResult()

    if message is None:
        result.add_error("message", "Message is required")
        return result

    if not isinstance(message, str):
        result.add_error("message", "Message must be a string")
        return result

    message_stripped = message.strip()
    if not message_stripped:
        result.add_error("message", "Message cannot be empty")
        return result

    if len(message_stripped) > MAX_MESSAGE_LENGTH:
        result.add_error(
            "message",
            f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters",
        )

    return result

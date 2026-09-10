"""Tests for agent input validation."""

import pytest
from src.agent.agent_schema import AgentRequest
from src.agent.input_validation import validate_request, validate_message


class TestValidateMessage:
    def test_valid_message(self):
        result = validate_message("Where is my order?")
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_empty_message(self):
        result = validate_message("")
        assert result.is_valid is False
        assert any(e.field == "message" for e in result.errors)

    def test_none_message(self):
        result = validate_message(None)
        assert result.is_valid is False

    def test_whitespace_only(self):
        result = validate_message("   ")
        assert result.is_valid is False

    def test_too_long(self):
        result = validate_message("x" * 10001)
        assert result.is_valid is False
        assert any("length" in e.message.lower() for e in result.errors)

    def test_non_string(self):
        result = validate_message(123)
        assert result.is_valid is False

    def test_valid_long_message(self):
        result = validate_message("x" * 9999)
        assert result.is_valid is True


class TestValidateRequest:
    def test_valid_request(self):
        request = AgentRequest(message="test message")
        result = validate_request(request)
        assert result.is_valid is True

    def test_empty_message(self):
        request = AgentRequest(message="")
        result = validate_request(request)
        assert result.is_valid is False

    def test_invalid_conversation_id(self):
        with pytest.raises(Exception):
            AgentRequest(message="test", conversation_id=123)

    def test_invalid_message_id(self):
        with pytest.raises(Exception):
            AgentRequest(message="test", message_id=456)

    def test_invalid_context(self):
        with pytest.raises(Exception):
            AgentRequest(message="test", conversation_context="invalid")

    def test_too_many_context(self):
        request = AgentRequest(
            message="test",
            conversation_context=[{"role": "customer"}] * 51,
        )
        result = validate_request(request)
        assert result.is_valid is False

    def test_valid_with_context(self):
        request = AgentRequest(
            message="test",
            conversation_id="conv_001",
            message_id="msg_001",
            conversation_context=[{"role": "customer", "content": "hi"}],
        )
        result = validate_request(request)
        assert result.is_valid is True

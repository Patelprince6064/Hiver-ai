"""Tests for LLM providers."""

import pytest
from src.generation.llm.base_provider import BaseLLMProvider, LLMResponse
from src.generation.llm.mock_provider import MockLLMProvider


class TestLLMResponse:
    def test_valid_response(self):
        r = LLMResponse(text="Hello", status="success")
        assert r.text == "Hello"
        assert r.status == "success"

    def test_error_response(self):
        r = LLMResponse(text="", status="provider_error", error_type="timeout")
        assert r.status == "provider_error"
        assert r.error_type == "timeout"


class TestMockLLMProvider:
    def test_returns_response(self):
        provider = MockLLMProvider(response="Test reply")
        result = provider.generate(prompt="Hello")
        assert result.text == "Test reply"
        assert result.status == "success"

    def test_deterministic(self):
        provider = MockLLMProvider(response="Same")
        r1 = provider.generate(prompt="A")
        r2 = provider.generate(prompt="B")
        assert r1.text == r2.text

    def test_tracks_calls(self):
        provider = MockLLMProvider()
        provider.generate(prompt="First")
        provider.generate(prompt="Second")
        assert provider._call_count == 2
        assert provider._last_prompt == "Second"

    def test_custom_status(self):
        provider = MockLLMProvider(status="provider_error")
        result = provider.generate(prompt="Test")
        assert result.status == "provider_error"

    def test_system_prompt_stored(self):
        provider = MockLLMProvider()
        provider.generate(prompt="Test", system_prompt="System")
        assert provider._last_system_prompt == "System"

    def test_get_params(self):
        provider = MockLLMProvider(response="X")
        params = provider.get_params()
        assert params["provider"] == "MockLLMProvider"
        assert params["response"] == "X"


class TestBaseLLMProvider:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseLLMProvider()

"""Tests for generic reply baseline."""

import pytest
from src.generation.generic_baseline import GenericReplyGenerator, GENERIC_REPLY


class TestGenericReplyGenerator:
    def test_returns_valid_reply(self):
        gen = GenericReplyGenerator()
        result = gen.generate("My order is late")
        assert result.reply is not None
        assert result.status == "success"
        assert result.generation_method == "generic_baseline"

    def test_always_returns_same_reply(self):
        gen = GenericReplyGenerator()
        r1 = gen.generate("Problem A")
        r2 = gen.generate("Problem B")
        assert r1.reply == r2.reply

    def test_custom_fallback(self):
        gen = GenericReplyGenerator(fallback_reply="Custom message")
        result = gen.generate("Test")
        assert result.reply == "Custom message"

    def test_intent_preserved(self):
        gen = GenericReplyGenerator()
        result = gen.generate("Test", intent="delivery_delay", intent_confidence=0.9)
        assert result.predicted_intent == "delivery_delay"
        assert result.intent_confidence == 0.9

    def test_no_evidence(self):
        gen = GenericReplyGenerator()
        result = gen.generate("Test")
        assert result.evidence == []

    def test_get_params(self):
        gen = GenericReplyGenerator()
        params = gen.get_params()
        assert "generator" in params

    def test_default_reply_matches_constant(self):
        gen = GenericReplyGenerator()
        assert gen.fallback_reply == GENERIC_REPLY

"""Tests for baselines.py — AlwaysAutoHandle, AlwaysEscalate."""

import pytest
from src.escalation.baselines import AlwaysAutoHandle, AlwaysEscalate


class TestAlwaysAutoHandle:
    def test_returns_auto_handle(self):
        b = AlwaysAutoHandle()
        d = b.evaluate()
        assert d.decision == "AUTO_HANDLE"
        assert d.risk_level == "LOW"
        assert d.confidence == 1.0
        assert "ALWAYS_AUTO_HANDLE_BASELINE" not in d.reason_codes

    def test_should_auto_handle(self):
        b = AlwaysAutoHandle()
        assert b.should_auto_handle() is True
        assert b.should_escalate() is False

    def test_get_params(self):
        b = AlwaysAutoHandle()
        p = b.get_params()
        assert p["strategy"] == "always_auto_handle"


class TestAlwaysEscalate:
    def test_returns_escalate(self):
        b = AlwaysEscalate()
        d = b.evaluate()
        assert d.decision == "ESCALATE_TO_HUMAN"
        assert d.risk_level == "HIGH"
        assert d.confidence == 1.0
        assert "ALWAYS_ESCALATE_BASELINE" in d.reason_codes

    def test_should_escalate(self):
        b = AlwaysEscalate()
        assert b.should_escalate() is True
        assert b.should_auto_handle() is False

    def test_get_params(self):
        b = AlwaysEscalate()
        p = b.get_params()
        assert p["strategy"] == "always_escalate"

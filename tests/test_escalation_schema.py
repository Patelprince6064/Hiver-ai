"""Tests for escalation_schema.py — EscalationDecision Pydantic model."""

import pytest
from src.escalation.escalation_schema import EscalationDecision, build_escalation_decision


class TestEscalationDecision:
    def test_create_auto_handle(self):
        d = EscalationDecision(
            decision="AUTO_HANDLE",
            reason_codes=[],
            risk_level="LOW",
            confidence=0.9,
            signals={},
            recommended_action="Handle with AI",
            policy_version="v1.0",
        )
        assert d.decision == "AUTO_HANDLE"
        assert d.risk_level == "LOW"

    def test_create_escalate(self):
        d = EscalationDecision(
            decision="ESCALATE_TO_HUMAN",
            reason_codes=["BILLING_CLAIM"],
            risk_level="HIGH",
            confidence=0.4,
            signals={},
            recommended_action="Escalate immediately",
            policy_version="v1.0",
        )
        assert d.decision == "ESCALATE_TO_HUMAN"
        assert "BILLING_CLAIM" in d.reason_codes

    def test_invalid_decision(self):
        with pytest.raises(Exception):
            EscalationDecision(
                decision="INVALID",
                reason_codes=[],
                risk_level="LOW",
                confidence=0.5,
                signals={},
                recommended_action="test",
                policy_version="v1.0",
            )

    def test_build_escalation_decision(self):
        d = build_escalation_decision(
            decision="AUTO_HANDLE",
            reason_codes=["LOW_INTENT_CONFIDENCE"],
            risk_level="MEDIUM",
            confidence=0.65,
            signals={"intent_confidence": 0.65},
            recommended_action="Check confidence",
        )
        assert d.decision == "AUTO_HANDLE"
        assert d.policy_version == "v1.0"
        assert d.signals["intent_confidence"] == 0.65

    def test_model_dump(self):
        d = EscalationDecision(
            decision="ESCALATE_TO_HUMAN",
            reason_codes=["BILLING_CLAIM", "LEGAL_THREATS"],
            risk_level="HIGH",
            confidence=0.3,
            signals={"intent_confidence": 0.3},
            recommended_action="Escalate",
            policy_version="v1.0",
        )
        result = d.model_dump()
        assert result["decision"] == "ESCALATE_TO_HUMAN"
        assert "BILLING_CLAIM" in result["reason_codes"]
        assert result["risk_level"] == "HIGH"
        assert result["confidence"] == 0.3

    def test_build_default_recommended_action(self):
        d = build_escalation_decision(decision="ESCALATE_TO_HUMAN")
        assert "Human review" in d.recommended_action

        d2 = build_escalation_decision(decision="AUTO_HANDLE")
        assert "generate" in d2.recommended_action

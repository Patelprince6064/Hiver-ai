"""Tests for rule_based_policy.py — RuleBasedPolicy."""

import pytest
from src.escalation.rule_based_policy import RuleBasedPolicy
from src.escalation.risk_signals import RiskSignals


def _make_signals(**kwargs) -> RiskSignals:
    defaults = {
        "intent_confidence": 0.85,
        "retrieval_available": True,
        "retrieval_status": "success",
        "grounding_status": "pass",
        "reply_valid": True,
        "has_high_risk_claims": False,
        "high_risk_claim_types": [],
        "has_unsupported_claims": False,
        "is_multi_intent": False,
        "is_ambiguous": False,
        "has_safety_risk": False,
        "is_provider_error": False,
        "requires_account_action": False,
        "requires_order_action": False,
        "has_financial_claim": False,
    }
    defaults.update(kwargs)
    return RiskSignals(**defaults)


class TestRuleBasedPolicy:
    def test_auto_handle_high_confidence(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(intent_confidence=0.85)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "AUTO_HANDLE"
        assert reason_codes == []

    def test_escalate_low_confidence(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(intent_confidence=0.5)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "LOW_INTENT_CONFIDENCE" in reason_codes

    def test_escalate_no_retrieval(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(retrieval_available=False, retrieval_status="no_evidence")
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "INSUFFICIENT_EVIDENCE" in reason_codes

    def test_escalate_grounding_fail(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(grounding_status="fail", has_high_risk_claims=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "GROUNDING_FAILURE" in reason_codes

    def test_escalate_high_risk(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(
            has_high_risk_claims=True,
            high_risk_claim_types=["price"],
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "HIGH_RISK_CLAIM" in reason_codes

    def test_escalate_ambiguous(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(is_ambiguous=True, intent_confidence=0.35)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"

    def test_escalate_multi_intent(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(is_multi_intent=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "MULTI_INTENT" in reason_codes

    def test_escalate_invalid_reply(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(reply_valid=False)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "INVALID_REPLY" in reason_codes

    def test_custom_threshold(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.90)
        signals = _make_signals(intent_confidence=0.85)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"

    def test_multiple_reason_codes(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(
            retrieval_available=False,
            retrieval_status="no_evidence",
            grounding_status="fail",
            is_ambiguous=True,
            is_multi_intent=True,
            intent_confidence=0.3,
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert len(reason_codes) >= 1

    def test_get_params(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.80)
        params = policy.get_params()
        assert params["min_intent_confidence"] == 0.80
        assert params["require_evidence"] is True

    def test_grounding_review_escalates(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(grounding_status="review")
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "GROUNDING_FAILURE" in reason_codes

    def test_insufficient_evidence_escalates(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(grounding_status="insufficient_evidence")
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"

    def test_provider_error_escalates(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(is_provider_error=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "PROVIDER_ERROR" in reason_codes

    def test_financial_claim_escalates(self):
        policy = RuleBasedPolicy(min_intent_confidence=0.70)
        signals = _make_signals(has_financial_claim=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "FINANCIAL_CLAIM" in reason_codes

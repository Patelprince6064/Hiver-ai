"""Tests for RiskAwarePolicy (v1.1) — rule_based_policy.py."""

import pytest
from src.escalation.rule_based_policy import RiskAwarePolicy, RuleBasedPolicy
from src.escalation.risk_signals import RiskSignals


def _make_signals(**kwargs) -> RiskSignals:
    defaults = {
        "intent_confidence": 0.85,
        "intent_top2_confidence": 0.10,
        "confidence_margin": 0.75,
        "retrieval_available": True,
        "retrieval_status": "success",
        "top_similarity": 0.8,
        "evidence_count": 3,
        "retrieval_quality_score": 0.7,
        "grounding_status": "pass",
        "grounding_score": 0.9,
        "has_high_risk_claims": False,
        "high_risk_claim_types": [],
        "has_unsupported_claims": False,
        "reply_valid": True,
        "reply_status": "success",
        "has_safety_risk": False,
        "is_provider_error": False,
        "is_multi_intent": False,
        "is_ambiguous": False,
        "requires_account_action": False,
        "requires_order_action": False,
        "requires_personal_info": False,
        "has_financial_claim": False,
        "is_high_risk_request": False,
        "high_risk_request_categories": [],
        "conversation_complexity_score": 0.2,
        "conversation_complexity_level": "low",
        "has_repeated_unresolved_issue": False,
    }
    defaults.update(kwargs)
    return RiskSignals(**defaults)


class TestRiskAwarePolicy:
    def test_auto_handle_safe_request(self):
        policy = RiskAwarePolicy(min_intent_confidence=0.70)
        signals = _make_signals(intent_confidence=0.85, confidence_margin=0.70)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "AUTO_HANDLE"
        assert reason_codes == []

    def test_escalate_provider_error(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(is_provider_error=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "PROVIDER_ERROR" in reason_codes

    def test_escalate_invalid_reply(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(reply_valid=False)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "INVALID_REPLY" in reason_codes

    def test_escalate_insufficient_evidence(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(retrieval_available=False, retrieval_status="no_evidence")
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "INSUFFICIENT_EVIDENCE" in reason_codes

    def test_escalate_grounding_failure(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(grounding_status="fail")
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "GROUNDING_FAILURE" in reason_codes

    def test_escalate_high_risk_claims(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(
            has_high_risk_claims=True,
            high_risk_claim_types=["price"],
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "HIGH_RISK_CLAIM" in reason_codes
        assert "UNSUPPORTED_PRICE" in reason_codes

    def test_escalate_high_risk_request(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(
            is_high_risk_request=True,
            high_risk_request_categories=["account_action"],
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "ACCOUNT_ACTION_REQUIRED" in reason_codes

    def test_escalate_low_confidence(self):
        policy = RiskAwarePolicy(min_intent_confidence=0.70)
        signals = _make_signals(intent_confidence=0.50, confidence_margin=0.30)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "LOW_INTENT_CONFIDENCE" in reason_codes

    def test_escalate_low_margin(self):
        policy = RiskAwarePolicy(min_intent_confidence=0.70, min_confidence_margin=0.15)
        signals = _make_signals(
            intent_confidence=0.72,
            intent_top2_confidence=0.60,
            confidence_margin=0.12,
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "LOW_INTENT_CONFIDENCE" in reason_codes

    def test_escalate_multi_intent(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(is_multi_intent=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "MULTI_INTENT" in reason_codes

    def test_escalate_ambiguous(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(is_ambiguous=True, intent_confidence=0.35, confidence_margin=0.10)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "AMBIGUOUS_REQUEST" in reason_codes

    def test_escalate_repeated_unresolved(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(has_repeated_unresolved_issue=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "REPEATED_UNRESOLVED" in reason_codes

    def test_escalate_high_complexity(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(
            conversation_complexity_score=0.8,
            conversation_complexity_level="high",
        )
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "COMPLEX_CASE" in reason_codes

    def test_escalate_safety_risk(self):
        policy = RiskAwarePolicy()
        signals = _make_signals(has_safety_risk=True)
        decision, reason_codes = policy.evaluate(signals)
        assert decision == "ESCALATE_TO_HUMAN"
        assert "SAFETY_RISK" in reason_codes

    def test_v10_remains_unchanged(self):
        v10 = RuleBasedPolicy(min_intent_confidence=0.70, policy_version="v1.0")
        signals = _make_signals(intent_confidence=0.85, confidence_margin=0.70)
        decision, reason_codes = v10.evaluate(signals)
        assert decision == "AUTO_HANDLE"

    def test_get_params(self):
        policy = RiskAwarePolicy(min_intent_confidence=0.80, min_confidence_margin=0.20)
        params = policy.get_params()
        assert params["policy_version"] == "v1.1"
        assert params["min_intent_confidence"] == 0.80
        assert params["min_confidence_margin"] == 0.20

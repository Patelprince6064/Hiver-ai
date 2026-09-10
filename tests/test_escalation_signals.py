"""Tests for risk_signals.py."""

import pytest
from src.escalation.risk_signals import RiskSignals, extract_signals, signals_to_dict


class TestExtractSignals:
    def test_basic_signals(self):
        intent_result = {"confidence": 0.8, "intent": "RETURNS"}
        retrieval_result = {"retrieval_status": "success", "results": [{"similarity_score": 0.7}]}
        grounding_result = {"status": "pass", "risk_flags": [], "unsupported_claims": []}
        reply_result = {"status": "success", "reply": "Hello", "risk_flags": []}

        signals = extract_signals(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            grounding_result=grounding_result,
            reply_result=reply_result,
        )
        assert signals.intent_confidence == 0.8
        assert signals.retrieval_available is True
        assert signals.grounding_status == "pass"
        assert signals.reply_valid is True

    def test_no_retrieval(self):
        intent_result = {"confidence": 0.8}
        retrieval_result = {"retrieval_status": "no_evidence", "results": []}
        grounding_result = {"status": "unknown", "risk_flags": [], "unsupported_claims": []}
        reply_result = {"status": "success", "reply": "Hello", "risk_flags": []}

        signals = extract_signals(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            grounding_result=grounding_result,
            reply_result=reply_result,
        )
        assert signals.retrieval_available is False
        assert signals.top_similarity is None

    def test_to_dict(self):
        intent_result = {"confidence": 0.6}
        retrieval_result = {"retrieval_status": "success", "results": [{"similarity_score": 0.5}]}
        grounding_result = {"status": "fail", "risk_flags": ["unsupported_high_risk_price"], "unsupported_claims": [{"type": "price"}]}
        reply_result = {"status": "success", "reply": "Test", "risk_flags": ["risky"]}

        signals = extract_signals(
            intent_result=intent_result,
            retrieval_result=retrieval_result,
            grounding_result=grounding_result,
            reply_result=reply_result,
        )
        d = signals_to_dict(signals)
        assert d["intent_confidence"] == 0.6
        assert d["retrieval_available"] is True
        assert d["grounding_status"] == "fail"
        assert d["has_high_risk_claims"] is True
        assert d["has_safety_risk"] is True

    def test_empty_results(self):
        signals = extract_signals()
        assert signals.intent_confidence is None
        assert signals.retrieval_available is False
        assert signals.top_similarity is None
        assert signals.grounding_status == "unknown"

    def test_multi_intent_detection(self):
        intent_result = {
            "confidence": 0.35,
            "intent": "RETURNS",
            "probabilities": {"RETURNS": 0.35, "BILLING": 0.30, "SHIPPING": 0.10},
        }
        signals = extract_signals(intent_result=intent_result)
        assert signals.is_multi_intent is True
        assert signals.is_ambiguous is True

    def test_provider_error(self):
        reply_result = {"status": "provider_error", "reply": None, "risk_flags": []}
        signals = extract_signals(reply_result=reply_result)
        assert signals.is_provider_error is True
        assert signals.reply_valid is False

    def test_high_risk_claims_from_grounding(self):
        grounding_result = {
            "status": "fail",
            "risk_flags": [],
            "unsupported_claims": [{"type": "price"}, {"type": "refund"}],
        }
        signals = extract_signals(grounding_result=grounding_result)
        assert signals.has_high_risk_claims is True

    def test_financial_claim_from_reply(self):
        reply_result = {"status": "success", "reply": "Test", "risk_flags": ["financial_claim"]}
        signals = extract_signals(reply_result=reply_result)
        assert signals.has_financial_claim is True

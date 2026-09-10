"""Tests for grounding_verifier (grounding_score + grounding_schema + grounding_metrics)."""

import pytest
from src.evaluation.grounding_score import compute_grounding_verdict
from src.evaluation.grounding_schema import build_grounding_verification, GroundingVerification
from src.evaluation.grounding_metrics import compute_grounding_metrics, GroundingMetrics
from src.evaluation.claim_extractor import Claim
from src.evaluation.evidence_support import SupportResult, check_claim_support
from src.evaluation.fact_types import FactType


@pytest.fixture
def evidence():
    return [
        {
            "knowledge_id": "KB-001",
            "customer_message": "My order hasn't arrived.",
            "support_response": "We have forwarded your request to the logistics team. You should receive an update within 24 hours.",
            "intent": "shipping",
            "resolution_type": "investigation",
        },
        {
            "knowledge_id": "KB-002",
            "customer_message": "Where is my package?",
            "support_response": "Please DM us your order number so we can track it.",
            "intent": "shipping",
            "resolution_type": "tracking",
        },
    ]


class TestGroundingVerdict:
    def test_empty_reply(self):
        verdict = compute_grounding_verdict("", [], [], evidence=[])
        assert verdict.status == "insufficient_evidence"

    def test_no_evidence(self):
        verdict = compute_grounding_verdict("Hello", [], [], evidence=[])
        assert verdict.status == "insufficient_evidence"

    def test_all_supported(self, evidence):
        claims = [
            Claim("please dm us your order number", FactType.INSTRUCTION, 0, 30),
        ]
        support_results = [check_claim_support(claims[0], evidence, "Help")]
        verdict = compute_grounding_verdict(
            "Please DM us your order number.", claims, support_results, evidence=evidence,
        )
        assert verdict.status == "pass"

    def test_unsupported_high_risk_fail(self, evidence):
        claims = [
            Claim("your order will arrive in 2 days", FactType.TIMELINE, 0, 30),
        ]
        support_results = [
            SupportResult("your order will arrive in 2 days", False, 0.1, "none", [], "No evidence."),
        ]
        verdict = compute_grounding_verdict(
            "Your order will arrive in 2 days.", claims, support_results, evidence=evidence,
        )
        assert verdict.status == "fail"
        assert any("unsupported_high_risk" in f for f in verdict.risk_flags)

    def test_unsupported_url_fail(self, evidence):
        class MockURLResult:
            passed = False
            unsupported = [type("U", (), {"url": "https://bad.com"})()]

        verdict = compute_grounding_verdict(
            "Visit https://bad.com",
            [],
            [],
            url_result=MockURLResult(),
            evidence=evidence,
        )
        assert verdict.status == "fail"

    def test_unsupported_numeric_fail(self, evidence):
        class MockNumResult:
            passed = False
            unsupported = [
                type("N", (), {"text": "₹9999", "category": "price"})(),
                type("N2", (), {"text": "₹8888", "category": "price"})(),
            ]

        verdict = compute_grounding_verdict(
            reply_text="Cost is ₹9999 and ₹8888.",
            claims=[],
            support_results=[],
            numeric_result=MockNumResult(),
            evidence=evidence,
        )
        assert verdict.status == "fail"

    def test_pii_leakage_fail(self, evidence):
        claims = []
        support_results = []

        class MockSafety:
            has_risk = True
            flags = ["contains_order_id"]

        verdict = compute_grounding_verdict(
            "Your order #12345 is on the way.",
            claims,
            support_results,
            pii_result=MockSafety(),
            evidence=evidence,
        )
        assert verdict.status == "fail"
        assert any("contains_order_id" in f for f in verdict.risk_flags)

    def test_one_unsupported_review(self, evidence):
        claims = [
            Claim("we have forwarded your request", FactType.ACTION, 0, 30),
        ]
        support_results = [
            SupportResult("we have forwarded your request", False, 0.1, "none", [], "Not found."),
        ]
        verdict = compute_grounding_verdict(
            "We have forwarded your request.", claims, support_results, evidence=evidence,
        )
        assert verdict.status == "review"

    def test_multiple_unsupported_fail(self, evidence):
        claims = [
            Claim("we guarantee 100% satisfaction", FactType.GUARANTEE, 0, 30),
            Claim("your order will arrive tomorrow", FactType.TIMELINE, 31, 61),
        ]
        support_results = [
            SupportResult("we guarantee 100% satisfaction", False, 0.1, "none", [], ""),
            SupportResult("your order will arrive tomorrow", False, 0.1, "none", [], ""),
        ]
        verdict = compute_grounding_verdict(
            "We guarantee 100% satisfaction. Your order will arrive tomorrow.",
            claims,
            support_results,
            evidence=evidence,
        )
        assert verdict.status == "fail"

    def test_low_semantic_review(self, evidence):
        class MockSemantic:
            passed = False
            overall_score = 0.1

        verdict = compute_grounding_verdict(
            "Some unrelated reply.",
            [],
            [],
            semantic_result=MockSemantic(),
            evidence=evidence,
        )
        assert verdict.status == "review"


class TestGroundingSchema:
    def test_build_grounding_verification(self):
        v = build_grounding_verification(
            status="pass",
            grounding_score=0.9,
            claims=[{"claim": "test", "type": "instruction", "supported": True}],
            risk_flags=[],
            reason="All supported.",
        )
        assert isinstance(v, GroundingVerification)
        assert v.status == "pass"
        assert v.grounding_score == 0.9
        assert len(v.claims) == 1
        assert v.claims[0].claim == "test"
        assert v.final_status == "pass"

    def test_repair_fields(self):
        v = build_grounding_verification(
            status="fail",
            repair_attempted=True,
            repair_succeeded=True,
            final_status="repaired",
        )
        assert v.repair_attempted is True
        assert v.repair_succeeded is True
        assert v.final_status == "repaired"

    def test_empty_build(self):
        v = build_grounding_verification(status="insufficient_evidence")
        assert v.status == "insufficient_evidence"
        assert v.claims == []
        assert v.risk_flags == []


class TestGroundingMetrics:
    def test_empty(self):
        m = compute_grounding_metrics([])
        assert m.n_replies == 0
        assert m.grounding_pass_rate == 0.0

    def test_all_pass(self):
        verifications = [
            {"status": "pass", "grounding_score": 0.9, "unsupported_claims": [], "risk_flags": []},
            {"status": "pass", "grounding_score": 0.8, "unsupported_claims": [], "risk_flags": []},
        ]
        m = compute_grounding_metrics(verifications)
        assert m.n_replies == 2
        assert m.grounding_pass_rate == 1.0
        assert m.unsupported_claim_rate == 0.0

    def test_mixed(self):
        verifications = [
            {"status": "pass", "grounding_score": 0.9, "unsupported_claims": [], "risk_flags": []},
            {"status": "fail", "grounding_score": 0.0, "unsupported_claims": [{"claim": "x"}], "risk_flags": ["unsupported_high_risk_price"]},
            {"status": "review", "grounding_score": 0.5, "unsupported_claims": [{"claim": "y"}], "risk_flags": []},
            {"status": "insufficient_evidence", "grounding_score": 0.0, "unsupported_claims": [], "risk_flags": []},
        ]
        m = compute_grounding_metrics(verifications)
        assert m.n_replies == 4
        assert m.grounding_pass_rate == 0.25
        assert m.high_risk_unsupported_rate == 0.25

    def test_repair_stats(self):
        verifications = [
            {"status": "fail", "grounding_score": 0.0, "unsupported_claims": [], "risk_flags": [], "repair_attempted": True, "repair_succeeded": True},
            {"status": "fail", "grounding_score": 0.0, "unsupported_claims": [], "risk_flags": [], "repair_attempted": True, "repair_succeeded": False},
        ]
        m = compute_grounding_metrics(verifications)
        assert m.repair_rate == 1.0
        assert m.repair_success_rate == 0.5

    def test_avg_score(self):
        verifications = [
            {"status": "pass", "grounding_score": 0.8, "unsupported_claims": [], "risk_flags": []},
            {"status": "pass", "grounding_score": 0.6, "unsupported_claims": [], "risk_flags": []},
        ]
        m = compute_grounding_metrics(verifications)
        assert abs(m.avg_grounding_score - 0.7) < 0.01

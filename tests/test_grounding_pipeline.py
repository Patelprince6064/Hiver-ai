"""Integration tests for the grounding pipeline."""

import pytest
from src.evaluation.claim_extractor import extract_claims
from src.evaluation.evidence_support import check_claim_support
from src.evaluation.numeric_claim_checker import check_numeric_claims
from src.evaluation.url_checker import check_urls
from src.evaluation.semantic_grounding import check_semantic_grounding
from src.evaluation.grounding_score import compute_grounding_verdict
from src.evaluation.grounding_metrics import compute_grounding_metrics
from src.evaluation.grounding_schema import build_grounding_verification
from src.evaluation.fact_types import FactType


@pytest.fixture
def evidence():
    return [
        {
            "knowledge_id": "KB-001",
            "customer_message": "My order hasn't arrived yet.",
            "support_response": "We have forwarded your request to the logistics team. You should receive an update within 24 hours.",
            "intent": "shipping",
            "resolution_type": "investigation",
        },
        {
            "knowledge_id": "KB-002",
            "customer_message": "Where is my package?",
            "support_response": "Please DM us your order number so we can track it for you.",
            "intent": "shipping",
            "resolution_type": "tracking",
        },
    ]


class TestGroundingPipeline:
    def test_full_pipeline_pass(self, evidence):
        reply = "Please DM us your order number so we can track it for you."
        customer_message = "Where is my package?"

        claims = extract_claims(reply)
        support_results = [check_claim_support(c, evidence, customer_message) for c in claims]
        numeric = check_numeric_claims(reply, evidence)
        url_check = check_urls(reply, evidence, customer_message)
        semantic = check_semantic_grounding(reply, evidence)

        verdict = compute_grounding_verdict(
            reply_text=reply,
            claims=claims,
            support_results=support_results,
            numeric_result=numeric,
            url_result=url_check,
            semantic_result=semantic,
            evidence=evidence,
        )

        assert verdict.status in ("pass", "review")
        assert verdict.grounding_score >= 0.0

    def test_full_pipeline_fail_high_risk(self, evidence):
        reply = "Your order will arrive in exactly 2 days and costs ₹599."
        customer_message = "When will my order arrive?"

        claims = extract_claims(reply)
        support_results = [check_claim_support(c, evidence, customer_message) for c in claims]
        numeric = check_numeric_claims(reply, evidence)
        url_check = check_urls(reply, evidence, customer_message)
        semantic = check_semantic_grounding(reply, evidence)

        verdict = compute_grounding_verdict(
            reply_text=reply,
            claims=claims,
            support_results=support_results,
            numeric_result=numeric,
            url_result=url_check,
            semantic_result=semantic,
            evidence=evidence,
        )

        assert verdict.status in ("fail", "review")

    def test_full_pipeline_with_url(self, evidence):
        reply = "Visit https://example.com/help for more details."
        customer_message = "How do I get help?"

        claims = extract_claims(reply)
        support_results = [check_claim_support(c, evidence, customer_message) for c in claims]
        numeric = check_numeric_claims(reply, evidence)
        url_check = check_urls(reply, evidence, customer_message)
        semantic = check_semantic_grounding(reply, evidence)

        verdict = compute_grounding_verdict(
            reply_text=reply,
            claims=claims,
            support_results=support_results,
            numeric_result=numeric,
            url_result=url_check,
            semantic_result=semantic,
            evidence=evidence,
        )

        assert verdict.status == "fail"
        assert any("unsupported_url" in f for f in verdict.risk_flags)

    def test_full_pipeline_empty_reply(self, evidence):
        verdict = compute_grounding_verdict(
            reply_text="",
            claims=[],
            support_results=[],
            evidence=evidence,
        )
        assert verdict.status == "insufficient_evidence"

    def test_metrics_integration(self, evidence):
        verifications = []
        for reply_text in [
            "Please DM us your order number.",
            "Your order costs ₹500 and arrives tomorrow.",
        ]:
            claims = extract_claims(reply_text)
            support_results = [check_claim_support(c, evidence, "test") for c in claims]
            verdict = compute_grounding_verdict(
                reply_text=reply_text,
                claims=claims,
                support_results=support_results,
                evidence=evidence,
            )
            verifications.append({
                "status": verdict.status,
                "grounding_score": verdict.grounding_score,
                "unsupported_claims": verdict.unsupported_claims,
                "risk_flags": verdict.risk_flags,
            })

        metrics = compute_grounding_metrics(verifications)
        assert metrics.n_replies == 2
        assert 0.0 <= metrics.grounding_pass_rate <= 1.0

    def test_schema_integration(self, evidence):
        reply = "Please DM us your order number."
        claims = extract_claims(reply)
        support_results = [check_claim_support(c, evidence, "test") for c in claims]
        verdict = compute_grounding_verdict(
            reply_text=reply,
            claims=claims,
            support_results=support_results,
            evidence=evidence,
        )

        verification = build_grounding_verification(
            status=verdict.status,
            grounding_score=verdict.grounding_score,
            claims=verdict.claims,
            risk_flags=verdict.risk_flags,
            unsupported_claims=verdict.unsupported_claims,
            evidence_used=verdict.evidence_used,
            reason=verdict.reason,
        )

        assert verification.status == verdict.status
        assert verification.grounding_score == verdict.grounding_score

    def test_claim_types_across_pipeline(self, evidence):
        replies = [
            "Please DM us your order number.",
            "We have forwarded your request to the team.",
            "Your order will arrive within 5 business days.",
            "The item costs ₹599.",
        ]
        for reply in replies:
            claims = extract_claims(reply)
            for claim in claims:
                assert isinstance(claim.fact_type, FactType)
                support = check_claim_support(claim, evidence, "test")
                assert support.supported is not None

    def test_numeric_in_pipeline(self, evidence):
        reply = "Delivery within 3 business days."
        claims = extract_claims(reply)
        support_results = [check_claim_support(c, evidence, "test") for c in claims]
        numeric = check_numeric_claims(reply, evidence)
        verdict = compute_grounding_verdict(
            reply_text=reply,
            claims=claims,
            support_results=support_results,
            numeric_result=numeric,
            evidence=evidence,
        )
        assert verdict.status in ("pass", "review", "fail")

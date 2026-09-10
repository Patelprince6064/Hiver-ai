"""Tests for evidence_support module."""

import pytest
from src.evaluation.evidence_support import check_claim_support, SupportResult
from src.evaluation.claim_extractor import Claim
from src.evaluation.fact_types import FactType


@pytest.fixture
def sample_evidence():
    return [
        {
            "knowledge_id": "KB-001",
            "customer_message": "My order hasn't arrived yet.",
            "support_response": "We have forwarded your request to our logistics team. You should receive an update within 24 hours.",
            "intent": "shipping",
            "resolution_type": "investigation",
        },
        {
            "knowledge_id": "KB-002",
            "customer_message": "Where is my order?",
            "support_response": "Please DM us your order number so we can track it for you.",
            "intent": "shipping",
            "resolution_type": "tracking",
        },
    ]


class TestEvidenceSupport:
    def test_exact_match(self, sample_evidence):
        claim = Claim(
            text="please dm us your order number so we can track it",
            fact_type=FactType.INSTRUCTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "My order hasn't arrived.")
        assert result.supported is True
        assert result.confidence >= 0.7
        assert result.support_source in ("evidence", "customer_message")

    def test_customer_message_match(self, sample_evidence):
        claim = Claim(
            text="my order hasn't arrived",
            fact_type=FactType.STATUS,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "My order hasn't arrived yet.")
        assert result.supported is True

    def test_partial_match(self, sample_evidence):
        claim = Claim(
            text="forwarded request logistics team",
            fact_type=FactType.ACTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "My order hasn't arrived.")
        assert result.supported is True

    def test_no_match(self, sample_evidence):
        claim = Claim(
            text="the system costs exactly ₹9999 per month",
            fact_type=FactType.PRICE,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "My order hasn't arrived.")
        assert result.supported is False

    def test_empty_evidence(self):
        claim = Claim(
            text="we will help you",
            fact_type=FactType.ACTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, [], "Help me please.")
        assert result.supported is False

    def test_empty_claim(self, sample_evidence):
        claim = Claim(
            text="",
            fact_type=FactType.OTHER,
            start=0,
            end=0,
        )
        result = check_claim_support(claim, sample_evidence, "Help me.")
        assert result.supported is False

    def test_entity_inference(self, sample_evidence):
        claim = Claim(
            text="forwarded request",
            fact_type=FactType.ACTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "Help me.")
        assert result.supported is True
        assert result.support_source == "evidence"

    def test_support_result_fields(self, sample_evidence):
        claim = Claim(
            text="please dm us your order number",
            fact_type=FactType.INSTRUCTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, sample_evidence, "Where is my order?")
        assert isinstance(result, SupportResult)
        assert result.claim_text == claim.text
        assert result.support_source in ("evidence", "customer_message", "none")
        assert isinstance(result.supporting_evidence_ids, list)
        assert isinstance(result.reason, str)

    def test_multiple_evidence_sources(self):
        evidence = [
            {
                "knowledge_id": "KB-100",
                "customer_message": "I need help.",
                "support_response": "Please DM us your order number.",
                "intent": "order",
                "resolution_type": "info",
            },
        ]
        claim = Claim(
            text="please dm us your order number",
            fact_type=FactType.INSTRUCTION,
            start=0,
            end=50,
        )
        result = check_claim_support(claim, evidence, "Help me.")
        assert result.supported is True
        assert "KB-100" in result.supporting_evidence_ids or result.support_source == "evidence"

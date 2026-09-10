"""Tests for claim_extractor module."""

import pytest
from src.evaluation.claim_extractor import extract_claims, Claim
from src.evaluation.fact_types import FactType


class TestClaimExtractor:
    def test_empty_text(self):
        assert extract_claims("") == []

    def test_whitespace_only(self):
        assert extract_claims("   ") == []

    def test_greeting_only(self):
        claims = extract_claims("Hello!")
        assert len(claims) == 0

    def test_meta_statement(self):
        claims = extract_claims("I am an AI assistant and I cannot help with that.")
        assert len(claims) == 0

    def test_single_instruction_claim(self):
        claims = extract_claims("Please DM us your order number.")
        assert len(claims) >= 1
        assert any("DM us" in c.text for c in claims)
        assert any(c.fact_type == FactType.INSTRUCTION for c in claims)

    def test_multiple_clauses(self):
        claims = extract_claims("We have processed your refund, you should see it within 3-5 days.")
        assert len(claims) >= 1

    def test_timeline_claim(self):
        claims = extract_claims("Your order will arrive within 5 business days.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.TIMELINE for c in claims)

    def test_price_claim(self):
        claims = extract_claims("The item costs ₹599.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.PRICE for c in claims)

    def test_guarantee_claim(self):
        claims = extract_claims("We guarantee a response within 24 hours.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.GUARANTEE for c in claims)

    def test_identifier_claim(self):
        claims = extract_claims("Please provide your order #12345.")
        assert len(claims) >= 1

    def test_action_claim(self):
        claims = extract_claims("We have forwarded your request to the team.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.ACTION for c in claims)

    def test_status_claim(self):
        claims = extract_claims("Your account status is active.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.STATUS for c in claims)

    def test_contact_method_claim(self):
        claims = extract_claims("You can email us at support@example.com.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.CONTACT_METHOD for c in claims)

    def test_technical_claim(self):
        claims = extract_claims("The system requires API version 2.0.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.TECHNICAL_CLAIM for c in claims)

    def test_claim_positions(self):
        text = "First sentence. Second sentence."
        claims = extract_claims(text)
        for claim in claims:
            assert 0 <= claim.start <= claim.end <= len(text)

    def test_claim_confidence(self):
        claims = extract_claims("We will help you resolve this.")
        for claim in claims:
            assert 0 <= claim.confidence <= 1.0

    def test_multi_sentence(self):
        text = "We understand your concern. Please DM us your order number. We will look into it immediately."
        claims = extract_claims(text)
        assert len(claims) >= 2

    def test_short_clauses_skipped(self):
        claims = extract_claims("Hi. OK.")
        short_claims = [c for c in claims if len(c.text.split()) < 2]
        assert len(short_claims) == 0

    def test_refund_claim_type(self):
        claims = extract_claims("We can process a refund for you.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.POLICY for c in claims)

    def test_quantity_claim(self):
        claims = extract_claims("You ordered 3 items total.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.QUANTITY for c in claims)

    def test_resolution_claim(self):
        claims = extract_claims("Your issue has been resolved.")
        assert len(claims) >= 1
        assert any(c.fact_type == FactType.RESOLUTION for c in claims)

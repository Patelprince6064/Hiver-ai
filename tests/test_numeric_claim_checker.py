"""Tests for numeric_claim_checker module."""

import pytest
from src.evaluation.numeric_claim_checker import (
    extract_numeric_claims,
    check_numeric_claims,
    NumericClaim,
    NumericCheckResult,
)


class TestExtractNumericClaims:
    def test_empty_text(self):
        assert extract_numeric_claims("") == []

    def test_price_claim(self):
        claims = extract_numeric_claims("The item costs ₹599.")
        assert len(claims) >= 1
        assert any(c.category == "price" for c in claims)

    def test_percentage_claim(self):
        claims = extract_numeric_claims("You get 10% off your next order.")
        assert len(claims) >= 1
        assert any(c.category == "percentage" for c in claims)

    def test_duration_claim(self):
        claims = extract_numeric_claims("Delivery will take 3-5 business days.")
        assert len(claims) >= 1
        assert any(c.category == "duration" for c in claims)

    def test_quantity_claim(self):
        claims = extract_numeric_claims("You ordered 5 items.")
        assert len(claims) >= 1
        assert any(c.category == "quantity" for c in claims)

    def test_date_claim(self):
        claims = extract_numeric_claims("Your order was placed on 12/25/2024.")
        assert len(claims) >= 1
        assert any(c.category == "date" for c in claims)

    def test_no_numbers(self):
        claims = extract_numeric_claims("Please contact us.")
        assert len(claims) == 0

    def test_multiple_categories(self):
        claims = extract_numeric_claims("₹500 refund in 3 days.")
        assert len(claims) >= 2
        categories = {c.category for c in claims}
        assert "price" in categories or "duration" in categories

    def test_claim_positions(self):
        text = "The price is ₹100."
        claims = extract_numeric_claims(text)
        for claim in claims:
            assert 0 <= claim.start <= claim.end <= len(text)

    def test_rs_prefix(self):
        claims = extract_numeric_claims("Cost is Rs. 1500.")
        assert len(claims) >= 1


class TestCheckNumericClaims:
    def test_supported_price(self):
        reply = "The item costs ₹599."
        evidence = [{"support_response": "Price is ₹599.", "customer_message": ""}]
        result = check_numeric_claims(reply, evidence)
        assert result.passed is True

    def test_unsupported_price(self):
        reply = "The item costs ₹9999."
        evidence = [{"support_response": "Price is ₹599.", "customer_message": ""}]
        result = check_numeric_claims(reply, evidence)
        assert result.passed is False
        assert len(result.unsupported) >= 1

    def test_supported_duration(self):
        reply = "Delivery within 3 business days."
        evidence = [{"support_response": "Delivery takes 3 business days from order.", "customer_message": ""}]
        result = check_numeric_claims(reply, evidence)
        assert result.passed is True

    def test_no_evidence(self):
        reply = "The cost is ₹500."
        result = check_numeric_claims(reply, [])
        assert result.passed is False

    def test_empty_reply(self):
        result = check_numeric_claims("", [{"support_response": "test"}])
        assert result.passed is True

    def test_no_numbers_in_reply(self):
        reply = "Please DM us."
        evidence = [{"support_response": "Contact us.", "customer_message": ""}]
        result = check_numeric_claims(reply, evidence)
        assert result.passed is True

    def test_result_fields(self):
        reply = "₹500 refund."
        result = check_numeric_claims(reply, [{"support_response": "test"}])
        assert isinstance(result, NumericCheckResult)
        assert isinstance(result.claims_found, list)
        assert isinstance(result.unsupported, list)
        assert isinstance(result.supported, list)
        assert isinstance(result.issues, list)

    def test_issue_messages(self):
        reply = "Cost is ₹9999."
        evidence = [{"support_response": "Price is ₹500.", "customer_message": ""}]
        result = check_numeric_claims(reply, evidence)
        for issue in result.issues:
            assert "Unsupported" in issue or "unsupported" in issue

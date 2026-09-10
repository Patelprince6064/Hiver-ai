"""Tests for grounding checks."""

import pytest
from src.evaluation.grounding_checks import (
    check_evidence_presence,
    check_evidence_ids_valid,
    check_historical_pii_leakage,
    check_unsupported_numeric_claims,
    check_historical_phrase_overlap,
    run_grounding_checks,
)


class TestEvidencePresence:
    def test_with_evidence(self):
        passed, _ = check_evidence_presence([{"knowledge_id": "kb_001"}])
        assert passed is True

    def test_without_evidence(self):
        passed, msg = check_evidence_presence([])
        assert passed is False
        assert "No evidence" in msg


class TestEvidenceIdsValid:
    def test_valid_ids(self):
        passed, _ = check_evidence_ids_valid(
            ["kb_001", "kb_002"], ["kb_001", "kb_002", "kb_003"]
        )
        assert passed is True

    def test_invalid_id(self):
        passed, msg = check_evidence_ids_valid(
            ["kb_001", "kb_999"], ["kb_001", "kb_002"]
        )
        assert passed is False
        assert "kb_999" in msg


class TestHistoricalPIILeakage:
    def test_no_leakage(self):
        evidence = [{"support_response": "DM us your order number."}]
        passed, _ = check_historical_pii_leakage(
            "Please DM us.", evidence, "My order is late"
        )
        assert passed is True

    def test_order_id_leakage(self):
        evidence = [{"support_response": "Order #ORD12345 is delayed."}]
        passed, msg = check_historical_pii_leakage(
            "Order #ORD12345 is delayed.", evidence, "Where is my order?"
        )
        assert passed is False
        assert "ORD12345" in msg

    def test_order_id_from_customer_ok(self):
        evidence = [{"support_response": "Order #ORD12345 is delayed."}]
        passed, _ = check_historical_pii_leakage(
            "Where is my order #ORD12345?", evidence, "Where is my order #ORD12345?"
        )
        assert passed is True


class TestUnsupportedNumericClaims:
    def test_no_claims(self):
        passed, _ = check_unsupported_numeric_claims("Hello", [])
        assert passed is True

    def test_supported_claim(self):
        evidence = [{"support_response": "Delivery in 3 days."}]
        passed, _ = check_unsupported_numeric_claims("Delivery in 3 days.", evidence)
        assert passed is True


class TestHistoricalPhraseOverlap:
    def test_good_overlap(self):
        evidence = [{"support_response": "Please DM us your order number."}]
        passed, _ = check_historical_phrase_overlap(
            "Please DM us your order number.", evidence
        )
        assert passed is True

    def test_low_overlap(self):
        evidence = [{"support_response": "Call 555-1234."}]
        passed, msg = check_historical_phrase_overlap(
            "The quantum entanglement theory suggests otherwise.", evidence
        )
        assert passed is False


class TestRunGroundingChecks:
    def test_all_pass(self):
        evidence = [{"knowledge_id": "kb_001", "support_response": "DM us."}]
        result = run_grounding_checks(
            reply="Please DM us.",
            evidence=evidence,
            customer_message="Help me",
        )
        assert result.passed is True

    def test_no_evidence(self):
        result = run_grounding_checks(
            reply="Hello",
            evidence=[],
            customer_message="Help",
        )
        assert result.passed is False
        assert "evidence_presence" in result.checks

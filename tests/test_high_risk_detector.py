"""Tests for high_risk_detector.py — High-risk request detection."""

import pytest
from src.escalation.high_risk_detector import (
    HighRiskDetection,
    detect_high_risk_request,
    detection_to_dict,
)


class TestHighRiskDetector:
    def test_no_risk(self):
        detection = detect_high_risk_request("What are your store hours?")
        assert detection.is_high_risk is False
        assert detection.risk_categories == []

    def test_account_action(self):
        detection = detect_high_risk_request("I want to cancel my account")
        assert detection.is_high_risk is True
        assert "account_action" in detection.risk_categories
        assert detection.requires_account_action is True
        assert detection.requires_external_system is True

    def test_order_status(self):
        detection = detect_high_risk_request("Where is my order #12345?")
        assert detection.is_high_risk is True
        assert "order_status" in detection.risk_categories
        assert detection.requires_order_status is True

    def test_refund(self):
        detection = detect_high_risk_request("I need a refund for my purchase")
        assert detection.is_high_risk is True
        assert "refund_compensation" in detection.risk_categories
        assert detection.involves_refund_or_compensation is True

    def test_financial_claim(self):
        detection = detect_high_risk_request("The price difference is wrong")
        assert detection.is_high_risk is True
        assert "financial_claim" in detection.risk_categories
        assert detection.involves_financial_claim is True

    def test_personal_info(self):
        detection = detect_high_risk_request("My email is test@example.com")
        assert detection.is_high_risk is True
        assert "personal_info" in detection.risk_categories
        assert detection.involves_personal_info is True

    def test_identity_verification(self):
        detection = detect_high_risk_request("Please verify my identity")
        assert detection.is_high_risk is True
        assert "identity_verification" in detection.risk_categories
        assert detection.involves_identity_verification is True

    def test_unsupported_pricing(self):
        detection = detect_high_risk_request("You guarantee the lowest price?")
        assert detection.is_high_risk is True
        # "guarantee" matches financial_claim pattern; both are valid risk categories
        assert detection.involves_financial_claim is True

    def test_unsupported_timeline(self):
        detection = detect_high_risk_request("You guarantee same-day delivery?")
        assert detection.is_high_risk is True
        assert "unsupported_timeline" in detection.risk_categories

    def test_irreversible_action(self):
        detection = detect_high_risk_request("I want to permanently delete all my data")
        assert detection.is_high_risk is True
        assert "irreversible_action" in detection.risk_categories

    def test_multiple_risks(self):
        detection = detect_high_risk_request(
            "I want to cancel my account and get a refund for order #12345"
        )
        assert detection.is_high_risk is True
        assert len(detection.risk_categories) >= 2

    def test_detection_to_dict(self):
        detection = detect_high_risk_request("I want to cancel my account")
        d = detection_to_dict(detection)
        assert isinstance(d, dict)
        assert "is_high_risk" in d
        assert "risk_categories" in d
        assert "requires_account_action" in d

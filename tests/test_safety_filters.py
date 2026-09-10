"""Tests for safety filters."""

import pytest
from src.generation.safety_filters import (
    detect_pii,
    detect_urls,
    detect_identifiers,
    detect_names,
    analyze_reply_safety,
)


class TestDetectPII:
    def test_email(self):
        flags = detect_pii("Email us at support@example.com")
        assert any(f.flag_type == "email" for f in flags)

    def test_phone(self):
        flags = detect_pii("Call 555-123-4567")
        assert any(f.flag_type == "phone_number" for f in flags)

    def test_clean(self):
        flags = detect_pii("Please DM us your order number.")
        assert len(flags) == 0


class TestDetectURLs:
    def test_url(self):
        flags = detect_urls("Visit https://example.com/help")
        assert any(f.flag_type == "url" for f in flags)

    def test_www(self):
        flags = detect_urls("Go to www.example.com")
        assert any(f.flag_type == "url" for f in flags)


class TestDetectIdentifiers:
    def test_order_id(self):
        flags = detect_identifiers("Your order ORD12345 is on the way.")
        assert any(f.flag_type == "order_id" for f in flags)

    def test_ticket(self):
        flags = detect_identifiers("Ticket #12345 has been created.")
        assert any(f.flag_type == "ticket_reference" for f in flags)

    def test_date(self):
        flags = detect_identifiers("Your order was placed on 12/25/2024.")
        assert any(f.flag_type == "date" for f in flags)


class TestDetectNames:
    def test_name(self):
        flags = detect_names("My name is John and I need help.")
        assert any(f.flag_type == "customer_name" for f in flags)


class TestAnalyzeReplySafety:
    def test_clean_reply(self):
        result = analyze_reply_safety("Please DM us your order number.")
        assert result.has_risk is False
        assert result.flags == []

    def test_risky_reply(self):
        result = analyze_reply_safety("Email john@example.com or call 555-123-4567.")
        assert result.has_risk is True
        assert "contains_email" in result.flags
        assert "contains_phone_number" in result.flags

    def test_url_risk(self):
        result = analyze_reply_safety("Visit https://example.com for more info.")
        assert "contains_url" in result.flags

    def test_order_id_risk(self):
        result = analyze_reply_safety("Order ORD12345 has been shipped.")
        assert "contains_order_id" in result.flags

    def test_empty_reply(self):
        result = analyze_reply_safety("")
        assert result.has_risk is False

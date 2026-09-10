"""Tests for url_checker module."""

import pytest
from src.evaluation.url_checker import extract_urls, check_urls, URLClaim, URLCheckResult


class TestExtractUrls:
    def test_empty_text(self):
        assert extract_urls("") == []

    def test_single_url(self):
        urls = extract_urls("Visit https://example.com for more info.")
        assert len(urls) == 1
        assert urls[0].url == "https://example.com"

    def test_multiple_urls(self):
        urls = extract_urls("See https://a.com and http://b.com.")
        assert len(urls) == 2

    def test_www_url(self):
        urls = extract_urls("Visit www.example.com.")
        assert len(urls) == 1

    def test_no_urls(self):
        urls = extract_urls("No links here.")
        assert len(urls) == 0

    def test_url_positions(self):
        text = "Visit https://example.com today."
        urls = extract_urls(text)
        assert len(urls) == 1
        url = urls[0]
        assert 0 <= url.start <= url.end <= len(text)

    def test_url_in_evidence(self):
        urls = extract_urls("Check https://help.example.com/faq")
        assert len(urls) == 1
        assert "help.example.com" in urls[0].url


class TestCheckUrls:
    def test_url_supported_in_evidence(self):
        reply = "Visit https://example.com/help for details."
        evidence = [{"support_response": "See https://example.com/help for FAQs.", "customer_message": ""}]
        result = check_urls(reply, evidence)
        assert result.passed is True

    def test_url_unsupported(self):
        reply = "Visit https://malicious.com for info."
        evidence = [{"support_response": "See https://example.com.", "customer_message": ""}]
        result = check_urls(reply, evidence)
        assert result.passed is False
        assert len(result.unsupported) >= 1

    def test_url_supported_in_customer_message(self):
        reply = "You can check https://example.com/track for updates."
        evidence = [{"support_response": "No URLs here.", "customer_message": ""}]
        customer_message = "I saw https://example.com/track on your site."
        result = check_urls(reply, evidence, customer_message)
        assert result.passed is True

    def test_no_urls(self):
        reply = "No links here."
        result = check_urls(reply, [{"support_response": "test"}])
        assert result.passed is True

    def test_empty_reply(self):
        result = check_urls("", [{"support_response": "test"}])
        assert result.passed is True

    def test_result_fields(self):
        reply = "Visit https://example.com."
        result = check_urls(reply, [{"support_response": "test"}])
        assert isinstance(result, URLCheckResult)
        assert isinstance(result.urls_found, list)
        assert isinstance(result.unsupported, list)
        assert isinstance(result.supported, list)
        assert isinstance(result.issues, list)

    def test_issue_messages(self):
        reply = "Visit https://bad.com."
        evidence = [{"support_response": "No URLs.", "customer_message": ""}]
        result = check_urls(reply, evidence)
        for issue in result.issues:
            assert "Unsupported URL" in issue

    def test_case_insensitive(self):
        reply = "Visit https://EXAMPLE.COM/help for details."
        evidence = [{"support_response": "See https://example.com/help for FAQs.", "customer_message": ""}]
        result = check_urls(reply, evidence)
        assert result.passed is True

    def test_multiple_unsupported(self):
        reply = "Check https://a.com and https://b.com."
        evidence = [{"support_response": "No URLs.", "customer_message": ""}]
        result = check_urls(reply, evidence)
        assert result.passed is False
        assert len(result.unsupported) == 2

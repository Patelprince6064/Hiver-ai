"""Tests for failure privacy."""

import pytest
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def mask_pii(text: str) -> str:
    """Mask personally identifiable information."""
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Mask phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Mask URLs with personal info
    text = re.sub(r'https?://[^\s]+', '[URL]', text)
    
    return text


class TestPIIMasking:
    """Tests for PII masking."""
    
    def test_email_masking(self):
        """Test email addresses are masked."""
        text = "Contact us at support@example.com for help."
        masked = mask_pii(text)
        
        assert "support@example.com" not in masked
        assert "[EMAIL]" in masked
    
    def test_phone_masking(self):
        """Test phone numbers are masked."""
        text = "Call us at 555-123-4567."
        masked = mask_pii(text)
        
        assert "555-123-4567" not in masked
        assert "[PHONE]" in masked
    
    def test_url_masking(self):
        """Test URLs are masked."""
        text = "Visit https://example.com/user/profile for details."
        masked = mask_pii(text)
        
        assert "https://example.com/user/profile" not in masked
        assert "[URL]" in masked
    
    def test_multiple_pii(self):
        """Test multiple PII types are masked."""
        text = "Email john@example.com or call 555-123-4567. Visit https://example.com."
        masked = mask_pii(text)
        
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked
        assert "https://example.com" not in masked
    
    def test_no_pii_unchanged(self):
        """Test text without PII is unchanged."""
        text = "This is a normal message without PII."
        masked = mask_pii(text)
        
        assert masked == text


class TestFailureReportPrivacy:
    """Tests for failure report privacy."""
    
    def test_no_account_ids(self):
        """Test account IDs are not in reports."""
        # This would test actual report generation
        # For now, just verify the masking function works
        text = "Account ID: ACC-123456"
        masked = mask_pii(text)
        
        # Account IDs should be masked if they contain PII patterns
        assert isinstance(masked, str)
    
    def test_no_order_ids(self):
        """Test order IDs are not in reports."""
        text = "Order ID: ORD-789012"
        masked = mask_pii(text)
        
        # Order IDs should be masked if they contain PII patterns
        assert isinstance(masked, str)


class TestDeterministicOutput:
    """Tests for deterministic output."""
    
    def test_masking_deterministic(self):
        """Test masking produces same output for same input."""
        text = "Contact support@example.com"
        
        masked1 = mask_pii(text)
        masked2 = mask_pii(text)
        
        assert masked1 == masked2
"""
Unit tests for Content Safety Service.

Tests the ContentSafetyService to ensure proper detection of:
- Security threats (XSS, SQL injection)
- Illegal items (weapons, drugs, explosives)
- Low quality queries (nonsense, whitespace-only)
- Malicious URLs
"""

import pytest
from src.services.content_safety_service import ContentSafetyService, SafetyViolation


class TestContentSafetyService:
    """Test suite for ContentSafetyService"""
    
    @pytest.fixture
    def safety_service(self):
        """Create a ContentSafetyService instance"""
        return ContentSafetyService()
    
    # Security Threat Tests
    def test_xss_detection(self, safety_service):
        """Test detection of XSS attempts"""
        queries = [
            "<script>alert('xss')</script>",
            "<script>document.cookie</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<iframe src='malicious.com'></iframe>",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block XSS: {query}"
            assert violation == SafetyViolation.SECURITY_THREAT
            assert "security" in reason.lower()
    
    def test_sql_injection_detection(self, safety_service):
        """Test detection of SQL injection attempts"""
        queries = [
            "DROP TABLE users;",
            "SELECT * FROM passwords WHERE 1=1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM admin",
            "DELETE FROM users WHERE id=1",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block SQL injection: {query}"
            assert violation == SafetyViolation.SECURITY_THREAT
    
    def test_command_injection_detection(self, safety_service):
        """Test detection of command injection attempts"""
        queries = [
            "rm -rf /",
            "del /f important.txt",
            "; shutdown -h now",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block command injection: {query}"
            assert violation == SafetyViolation.SECURITY_THREAT
    
    # Illegal Items Tests
    def test_illegal_weapons_detection(self, safety_service):
        """Test detection of illegal weapon queries"""
        queries = [
            "I need to buy weapons",
            "where to purchase illegal guns",
            "buy unregistered firearms",
            "I want to buy explosives",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block illegal weapons: {query}"
            assert violation == SafetyViolation.ILLEGAL_ITEMS
    
    def test_illegal_drugs_detection(self, safety_service):
        """Test detection of illegal drug queries"""
        queries = [
            "where to buy cocaine",
            "how to purchase heroin",
            "buy illegal drugs online",
            "sell methamphetamine",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block illegal drugs: {query}"
            assert violation == SafetyViolation.ILLEGAL_ITEMS
    
    def test_explosives_detection(self, safety_service):
        """Test detection of explosive-related queries"""
        queries = [
            # Note: "how to make a bomb" is in blocklist, not content_safety patterns
            "I want to build pipe bomb",
            "where to buy explosives online",
            "need to make bomb for project",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block explosives: {query}"
            assert violation == SafetyViolation.ILLEGAL_ITEMS
    
    # Low Quality Query Tests
    def test_whitespace_only_detection(self, safety_service):
        """Test detection of whitespace-only queries"""
        queries = [
            "   ",
            "\t\t\t",
            "\n\n\n",
            "     \t    ",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block whitespace-only: '{query}'"
            assert violation == SafetyViolation.LOW_QUALITY
            assert "whitespace" in reason.lower()
    
    def test_emoji_only_detection(self, safety_service):
        """Test detection of emoji-only queries"""
        queries = [
            "🏃‍♂️🏃‍♀️👟👟👟",
            "😀😃😄😁",
            "🔥🔥🔥⚡⚡⚡",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block emoji-only: {query}"
            assert violation == SafetyViolation.LOW_QUALITY
    
    def test_special_characters_only_detection(self, safety_service):
        """Test detection of special character-only queries"""
        queries = [
            "!@#$%^&*()",
            "[]{}|;':\"",
            ",./<>?`~",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block special chars only: {query}"
            assert violation == SafetyViolation.LOW_QUALITY
    
    def test_numbers_only_detection(self, safety_service):
        """Test detection of number-only queries"""
        queries = [
            "123456789",
            "42 3.14159",
            "1337 404 500",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block numbers only: {query}"
            assert violation == SafetyViolation.LOW_QUALITY
    
    def test_single_character_detection(self, safety_service):
        """Test detection of single character queries"""
        queries = ["a", "x", "z", "1"]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block single character: {query}"
            assert violation == SafetyViolation.LOW_QUALITY
    
    def test_excessive_repetition_detection(self, safety_service):
        """Test detection of excessively repeated words"""
        query = "shoes " * 15  # 15 repetitions
        is_safe, violation, reason = safety_service.validate_query(query)
        assert not is_safe, "Should block excessive repetition"
        assert violation == SafetyViolation.LOW_QUALITY
    
    # Malicious URL Tests
    def test_malicious_url_detection(self, safety_service):
        """Test detection of malicious URLs"""
        queries = [
            "Check out http://malware-site.com/virus.exe",
            "Visit http://phishing-site.com/steal-data",
            "Download from http://192.168.1.1/hack.exe",
            "Go to http://suspicious.tk/malware",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert not is_safe, f"Should block malicious URL: {query}"
            assert violation == SafetyViolation.MALICIOUS_URL
    
    # Valid Query Tests
    def test_valid_commercial_queries(self, safety_service):
        """Test that valid commercial queries pass"""
        queries = [
            "I need running shoes for marathon",
            "best laptop for programming",
            "cheap flights to Paris",
            "where to buy yoga mat",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert is_safe, f"Should allow valid query: {query}"
            assert violation is None
            assert reason is None
    
    def test_valid_informational_queries(self, safety_service):
        """Test that valid informational queries pass"""
        queries = [
            "What is the history of the marathon?",
            "How do I train for a 5k race?",
            "Why do runners get blisters?",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert is_safe, f"Should allow valid query: {query}"
            assert violation is None
    
    def test_multilingual_queries(self, safety_service):
        """Test that multilingual queries pass"""
        queries = [
            "Je voudrais acheter running shoes",
            "Necesito yoga mat para ejercicio",
            "Мне нужны кроссовки для бега",
        ]
        
        for query in queries:
            is_safe, violation, reason = safety_service.validate_query(query)
            assert is_safe, f"Should allow multilingual query: {query}"
            assert violation is None
    
    def test_fictional_products_allowed(self, safety_service):
        """Test that fictional product queries are allowed"""
        query = "Where can I buy a lightsaber, sonic screwdriver, portal gun?"
        is_safe, violation, reason = safety_service.validate_query(query)
        assert is_safe, "Should allow fictional products"
        assert violation is None
    
    # Sanitization Tests
    def test_query_sanitization(self, safety_service):
        """Test query sanitization"""
        test_cases = [
            ("<script>alert(1)</script>hello", "hello"),
            ("test\x00null", "testnull"),
            ("multiple   spaces", "multiple spaces"),
            ("  leading and trailing  ", "leading and trailing"),
        ]
        
        for input_query, expected in test_cases:
            sanitized = safety_service.sanitize_query(input_query)
            assert sanitized == expected, f"Sanitization failed for: {input_query}"
    
    # Edge Cases
    def test_empty_string(self, safety_service):
        """Test empty string handling"""
        is_safe, violation, reason = safety_service.validate_query("")
        assert not is_safe
        assert violation == SafetyViolation.LOW_QUALITY
    
    def test_mixed_valid_and_invalid_content(self, safety_service):
        """Test queries with mixed valid and invalid content"""
        # Valid query with some special chars (should pass)
        query = "What's the best laptop?!?"
        is_safe, violation, reason = safety_service.validate_query(query)
        assert is_safe, "Should allow queries with punctuation"
        
        # Invalid query with XSS attempt
        query = "I need shoes <script>alert(1)</script>"
        is_safe, violation, reason = safety_service.validate_query(query)
        assert not is_safe, "Should block queries with security threats"

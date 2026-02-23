"""
SERVICE: Content safety and query validation.

This service provides comprehensive content filtering, security threat detection,
and query quality validation to protect the ad system from malicious or
inappropriate content.
"""

import re
from typing import Tuple, Optional, List
from enum import Enum


class SafetyViolation(Enum):
    """Types of safety violations."""
    ILLEGAL_ITEMS = "illegal_items"
    SECURITY_THREAT = "security_threat"
    LOW_QUALITY = "low_quality"
    MALICIOUS_URL = "malicious_url"
    INJECTION_ATTEMPT = "injection_attempt"


class ContentSafetyService:
    """
    SERVICE: Content safety and query validation.
    
    Provides multi-layered protection:
    1. Query quality validation (nonsense, whitespace-only)
    2. Security threat detection (XSS, SQL injection)
    3. Illegal content detection (weapons, drugs, explosives)
    4. Malicious URL detection
    5. Query sanitization
    """
    
    def __init__(self):
        """Initialize the content safety service."""
        self.illegal_patterns = self._compile_illegal_patterns()
        self.security_patterns = self._compile_security_patterns()
        self.malicious_url_patterns = self._compile_malicious_url_patterns()
        self.quality_patterns = self._compile_quality_patterns()
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[SafetyViolation], Optional[str]]:
        """
        Validate query for safety and quality issues.
        
        Args:
            query: The query text to validate
            
        Returns:
            Tuple of (is_safe, violation_type, reason)
            - is_safe: True if query passes all checks
            - violation_type: Type of violation if any
            - reason: Human-readable reason for rejection
        """
        # 1. Check for whitespace-only or empty content
        if not query or query.strip() == "":
            return False, SafetyViolation.LOW_QUALITY, "Query contains only whitespace"
        
        # 2. Check for meaningful content (not just special characters/emojis)
        if not self._has_meaningful_content(query):
            return False, SafetyViolation.LOW_QUALITY, "Query lacks meaningful text content"
        
        # 3. Check for illegal items (weapons, drugs, explosives)
        if self._contains_illegal_items(query):
            return False, SafetyViolation.ILLEGAL_ITEMS, "Query contains references to illegal items"
        
        # 4. Check for security threats (XSS, SQL injection)
        if self._contains_security_threats(query):
            return False, SafetyViolation.SECURITY_THREAT, "Query contains potential security threats"
        
        # 5. Check for malicious URLs
        if self._contains_malicious_urls(query):
            return False, SafetyViolation.MALICIOUS_URL, "Query contains suspicious URLs"
        
        return True, None, None
    
    def sanitize_query(self, query: str) -> str:
        """
        Sanitize query by removing potentially harmful content.
        
        Args:
            query: The query text to sanitize
            
        Returns:
            Sanitized query text
        """
        # Strip HTML/script tags and their content
        query = re.sub(r'<script[^>]*>.*?</script>', '', query, flags=re.IGNORECASE | re.DOTALL)
        query = re.sub(r'<[^>]+>', '', query)
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query
    
    def _has_meaningful_content(self, query: str) -> bool:
        """
        Check if query has meaningful text content.
        
        A query is considered meaningful if it contains at least:
        - 2 alphanumeric characters, AND
        - 1 word of 2+ letters (any alphabet, not just Latin), AND
        - Not excessive repetition
        
        This filters out queries like:
        - Only emojis
        - Only special characters
        - Only numbers
        - Single characters
        - Excessive word repetition
        
        Args:
            query: Query text to check
            
        Returns:
            True if query has meaningful content
        """
        # Count alphanumeric characters
        alphanumeric_count = sum(c.isalnum() for c in query)
        
        # If we have very few alphanumeric characters, it's likely nonsense
        if alphanumeric_count < 2:
            return False
        
        # Check for at least one word with 2+ letters (any alphabet)
        # This includes Latin, Cyrillic, Chinese, etc.
        words = re.findall(r'\b[\w]{2,}\b', query, re.UNICODE)
        if not words:
            return False
        
        # Filter to only alphabetic words (exclude pure numbers)
        alpha_words = [w for w in words if any(c.isalpha() for c in w)]
        if not alpha_words:
            return False
        
        # Check for excessive repetition (same word 10+ times)
        # This catches "shoes shoes shoes..." but allows some repetition
        word_counts = {}
        for word in alpha_words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # If any single word appears more than 10 times, it's likely spam
        if any(count > 10 for count in word_counts.values()):
            return False
        
        return True
    
    def _contains_illegal_items(self, query: str) -> bool:
        """
        Check if query references illegal items.
        
        Detects references to:
        - Weapons (guns, explosives, bombs)
        - Illegal drugs
        - Illegal substances
        
        Args:
            query: Lowercased query text
            
        Returns:
            True if query contains illegal item references
        """
        query_lower = query.lower()
        return any(pattern.search(query_lower) for pattern in self.illegal_patterns)
    
    def _contains_security_threats(self, query: str) -> bool:
        """
        Check if query contains security threats.
        
        Detects:
        - XSS attempts (script tags, javascript:, onerror=, etc.)
        - SQL injection patterns (DROP, SELECT *, UNION, etc.)
        - Command injection patterns (rm -rf, etc.)
        
        Args:
            query: Query text to check
            
        Returns:
            True if query contains security threats
        """
        return any(pattern.search(query) for pattern in self.security_patterns)
    
    def _contains_malicious_urls(self, query: str) -> bool:
        """
        Check if query contains suspicious URLs.
        
        Detects URLs with:
        - Suspicious keywords (malware, phishing, steal, hack)
        - Executable file extensions (.exe, .bat, .sh)
        - IP addresses instead of domains
        
        Args:
            query: Query text to check
            
        Returns:
            True if query contains malicious URLs
        """
        query_lower = query.lower()
        return any(pattern.search(query_lower) for pattern in self.malicious_url_patterns)
    
    def _compile_illegal_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for illegal item detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Weapons - with intent context
            re.compile(r'\b(buy|purchase|need|want|sell)\s+(illegal\s+)?(gun|guns|firearm|firearms|weapon|weapons)\b', re.IGNORECASE),
            re.compile(r'\b(illegal|unregistered)\s+(gun|guns|firearm|firearms|weapon|weapons)\b', re.IGNORECASE),
            
            # Explosives - with intent context
            re.compile(r'\b(buy|make|build|create)\s+(explosive|explosives|bomb|bombs)\b', re.IGNORECASE),
            re.compile(r'\b(pipe\s+bomb|car\s+bomb|suicide\s+bomb)\b', re.IGNORECASE),
            
            # Illegal drugs - with clear intent
            re.compile(r'\b(buy|purchase|sell|deal)\s+(cocaine|heroin|methamphetamine|meth|crack|drugs)\b', re.IGNORECASE),
            re.compile(r'\b(illegal\s+(drug|drugs|substance|substances))\b', re.IGNORECASE),
            re.compile(r'\b(where\s+to\s+buy|how\s+to\s+get)\s+(cocaine|heroin|meth|drugs)\b', re.IGNORECASE),
        ]
        return patterns
    
    def _compile_security_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for security threat detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # XSS patterns
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<script[^>]*>', re.IGNORECASE),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on(error|load|click|mouse|focus|blur)\s*=', re.IGNORECASE),
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'alert\s*\(', re.IGNORECASE),
            
            # SQL injection patterns
            re.compile(r'\b(DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+TABLE)\b', re.IGNORECASE),
            re.compile(r'\b(SELECT\s+\*\s+FROM|UNION\s+SELECT)\b', re.IGNORECASE),
            re.compile(r'(--|#|/\*|\*/)\s*(DROP|DELETE|INSERT|UPDATE)', re.IGNORECASE),
            re.compile(r"('\s*(OR|AND)\s*'?\d*\s*'?\s*=\s*'?\d*)", re.IGNORECASE),
            
            # Command injection patterns
            re.compile(r'\b(rm\s+-rf|del\s+/f|format\s+c:)\b', re.IGNORECASE),
            re.compile(r'[;&|]\s*(rm|del|format|shutdown)', re.IGNORECASE),
        ]
        return patterns
    
    def _compile_malicious_url_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for malicious URL detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Suspicious keywords in URLs
            re.compile(r'https?://[^\s]*?(malware|virus|phishing|steal|hack|crack|keylog)', re.IGNORECASE),
            
            # Executable file extensions in URLs
            re.compile(r'https?://[^\s]*?\.(exe|bat|sh|cmd|vbs|ps1|dll)', re.IGNORECASE),
            
            # IP addresses instead of domains (often suspicious)
            re.compile(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', re.IGNORECASE),
            
            # Suspicious TLDs
            re.compile(r'https?://[^\s]*?\.(tk|ml|ga|cf|gq)/', re.IGNORECASE),
        ]
        return patterns
    
    def _compile_quality_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for query quality checks.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Detect excessive repetition (same word 5+ times)
            re.compile(r'\b(\w+)(\s+\1){4,}\b', re.IGNORECASE),
        ]
        return patterns

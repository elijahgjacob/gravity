"""
REPOSITORY: Data access for safety blocklist.

This repository handles loading and querying the safety blocklist
used to identify queries where ads should not be shown.
"""

import re
from typing import Set, List


class BlocklistRepository:
    """
    REPOSITORY: Data access for safety blocklist.
    
    Loads blocked terms and patterns from a text file and provides
    fast lookup methods for content filtering.
    """
    
    def __init__(self, blocklist_path: str):
        """
        Initialize the blocklist repository.
        
        Args:
            blocklist_path: Path to the blocklist text file
        """
        self.blocked_terms: Set[str] = set()
        self.blocked_patterns: List[re.Pattern] = []
        self._load_blocklist(blocklist_path)
    
    def _load_blocklist(self, path: str) -> None:
        """
        Load blocklist from file.
        
        Each line in the file is treated as a blocked term.
        Lines starting with '#' are treated as comments.
        Empty lines are ignored.
        
        Args:
            path: Path to the blocklist file
        """
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip whitespace
                term = line.strip().lower()
                
                # Skip comments and empty lines
                if not term or term.startswith('#'):
                    continue
                
                # Add to blocked terms set
                self.blocked_terms.add(term)
                
                # Compile as regex pattern for word boundary matching
                # This ensures we match whole words, not substrings
                escaped_term = re.escape(term)
                pattern = re.compile(rf'\b{escaped_term}\b', re.IGNORECASE)
                self.blocked_patterns.append(pattern)
    
    def contains_blocked_content(self, query: str) -> bool:
        """
        Check if query contains blocked content.
        
        Performs both exact substring matching and pattern matching
        with word boundaries to catch variations.
        
        Args:
            query: The query text to check
            
        Returns:
            True if query contains blocked content, False otherwise
        """
        query_lower = query.lower()
        
        # Fast path: Check for exact substring matches
        for term in self.blocked_terms:
            if term in query_lower:
                return True
        
        # Thorough path: Check pattern matches with word boundaries
        for pattern in self.blocked_patterns:
            if pattern.search(query):
                return True
        
        return False
    
    def get_blocked_terms_count(self) -> int:
        """
        Get the number of blocked terms loaded.
        
        Returns:
            Count of blocked terms
        """
        return len(self.blocked_terms)

"""
SERVICE: Business logic for ad eligibility scoring.

This service determines whether it's appropriate to show ads for a given query
by analyzing content for safety concerns, sensitive topics, and commercial intent.
"""

import re
from typing import Optional, List
from src.repositories.blocklist_repository import BlocklistRepository


class EligibilityService:
    """
    SERVICE: Business logic for ad eligibility scoring.
    
    Determines if it's appropriate to show ads for a query (0.0-1.0).
    
    Score ranges:
    - 0.0: Do not show ads (harmful/inappropriate content)
    - 0.3-0.5: Sensitive context (financial distress, grief, mental health)
    - 0.7-0.85: Informational queries (neutral)
    - 0.8-1.0: Commercial intent (appropriate for ads)
    """
    
    def __init__(self, blocklist_repo: BlocklistRepository):
        """
        Initialize the eligibility service.
        
        Args:
            blocklist_repo: Repository for accessing safety blocklist
        """
        self.blocklist_repo = blocklist_repo
        self.sensitive_patterns = self._compile_sensitive_patterns()
        self.commercial_patterns = self._compile_commercial_patterns()
    
    async def score(self, query: str, context: Optional[dict] = None) -> float:
        """
        Score query eligibility for ads.
        
        Args:
            query: The user's query text
            context: Optional user context (demographics, interests, etc.)
        
        Returns:
            Score from 0.0 to 1.0:
            - 0.0 = Do not show ads (harmful/inappropriate)
            - 0.4-0.7 = Sensitive context
            - 0.8-1.0 = Appropriate for ads
        """
        query_lower = query.lower()
        
        # Priority 1: Check blocklist (0.0 cases)
        # These are hard blocks for safety: self-harm, violence, NSFW, etc.
        if self.blocklist_repo.contains_blocked_content(query_lower):
            return 0.0
        
        # Priority 2: Check sensitive topics (0.3-0.5)
        # Financial distress, grief, mental health crises
        if self._is_sensitive(query_lower):
            return 0.4
        
        # Priority 3: Check commercial intent signals (0.8-1.0)
        # "buy", "best", "review", "price", etc.
        if self._has_commercial_intent(query_lower):
            return 0.95
        
        # Default: Informational queries (0.7-0.85)
        # General questions, how-to queries, etc.
        return 0.75
    
    def _is_sensitive(self, query: str) -> bool:
        """
        Check if query contains sensitive topics.
        
        Sensitive topics include:
        - Financial distress (bankruptcy, unemployment, debt)
        - Grief and loss (death, funeral, passed away)
        - Mental health crises (depression, anxiety, panic)
        - Medical emergencies (not in blocklist but sensitive)
        
        Args:
            query: Lowercased query text
            
        Returns:
            True if query contains sensitive content
        """
        return any(pattern.search(query) for pattern in self.sensitive_patterns)
    
    def _has_commercial_intent(self, query: str) -> bool:
        """
        Check if query has commercial intent signals.
        
        Commercial intent signals include:
        - Purchase keywords: buy, purchase, shop, order
        - Research keywords: best, top, review, compare
        - Price keywords: price, cost, cheap, deal, discount
        
        Args:
            query: Lowercased query text
            
        Returns:
            True if query has commercial intent
        """
        return any(pattern.search(query) for pattern in self.commercial_patterns)
    
    def _compile_sensitive_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for sensitive content detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Financial distress
            re.compile(r'\b(unemployed|unemployment|fired|laid off|layoff)\b', re.IGNORECASE),
            re.compile(r'\b(debt collector|repossession)\b', re.IGNORECASE),
            re.compile(r'\b(can\'?t pay|behind on payments|financial crisis)\b', re.IGNORECASE),
            
            # Grief and loss
            re.compile(r'\b(passed away|died|death|funeral|grief|grieving|mourning)\b', re.IGNORECASE),
            re.compile(r'\b(lost (my|our) (mom|dad|mother|father|son|daughter|child))\b', re.IGNORECASE),
            
            # Mental health crises
            re.compile(r'\b(depressed|depression|anxious|anxiety|panic attack)\b', re.IGNORECASE),
            re.compile(r'\b(mental breakdown|nervous breakdown|suicidal thoughts)\b', re.IGNORECASE),
            re.compile(r'\b(can\'?t cope|feeling hopeless|want to die)\b', re.IGNORECASE),
            
            # Medical emergencies (borderline)
            re.compile(r'\b(heart attack|stroke|overdose|emergency room)\b', re.IGNORECASE),
        ]
        return patterns
    
    def _compile_commercial_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for commercial intent detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Purchase intent (specific contexts)
            re.compile(r'\b(buy|purchase|shop|order|acquire)\b', re.IGNORECASE),
            re.compile(r'\b(where to (buy|get|find|purchase))\b', re.IGNORECASE),
            re.compile(r'\b(want to (buy|get|purchase))\b', re.IGNORECASE),
            re.compile(r'\b(need (to buy|to get|to purchase|new))\b', re.IGNORECASE),
            
            # Research intent
            re.compile(r'\b(best|top|review|compare|comparison|versus|vs)\b', re.IGNORECASE),
            re.compile(r'\b(recommend|recommendation|suggest|suggestion)\b', re.IGNORECASE),
            
            # Price intent
            re.compile(r'\b(price|cost|cheap|affordable|deal|discount|sale)\b', re.IGNORECASE),
            re.compile(r'\b(how much|pricing|budget)\b', re.IGNORECASE),
            
            # Product queries
            re.compile(r'\b(should i buy|worth buying|good deal)\b', re.IGNORECASE),
        ]
        return patterns

"""
SERVICE: Business logic for ad eligibility scoring.

This service determines whether it's appropriate to show ads for a given query
by analyzing content for safety concerns, sensitive topics, and commercial intent.
"""

import re
from typing import Optional, List, Tuple
from src.repositories.blocklist_repository import BlocklistRepository
from src.services.content_safety_service import ContentSafetyService


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
    
    def __init__(self, blocklist_repo: BlocklistRepository, content_safety_service: Optional[ContentSafetyService] = None):
        """
        Initialize the eligibility service.
        
        Args:
            blocklist_repo: Repository for accessing safety blocklist
            content_safety_service: Optional content safety service for additional validation
        """
        self.blocklist_repo = blocklist_repo
        self.content_safety_service = content_safety_service or ContentSafetyService()
        self.sensitive_patterns = self._compile_sensitive_patterns()
        self.commercial_patterns = self._compile_commercial_patterns()
    
    async def score(self, query: str, context: Optional[dict] = None) -> Tuple[float, Optional[str]]:
        """
        Score query eligibility for ads.
        
        Args:
            query: The user's query text
            context: Optional user context (demographics, interests, etc.)
        
        Returns:
            Tuple of (score, rejection_reason):
            - score: 0.0 to 1.0 (0.0 = blocked, 0.4-0.7 = sensitive, 0.8-1.0 = appropriate)
            - rejection_reason: Human-readable reason if score is 0.0, None otherwise
        """
        # Priority 0: Content safety validation (NEW)
        # Check for illegal items, security threats, low quality queries
        is_safe, violation_type, reason = self.content_safety_service.validate_query(query)
        if not is_safe:
            return 0.0, reason
        
        # Sanitize query for further processing
        query = self.content_safety_service.sanitize_query(query)
        query_lower = query.lower()
        
        # Priority 1: Check blocklist (0.0 cases)
        # These are hard blocks for safety: self-harm, violence, NSFW, etc.
        if self.blocklist_repo.contains_blocked_content(query_lower):
            return 0.0, "Query contains blocked content (safety violation)"
        
        # Priority 2: Check sensitive topics (0.3-0.5)
        # Financial distress, grief, mental health crises
        if self._is_sensitive(query_lower):
            return 0.4, None
        
        # Priority 3: Check commercial intent signals (0.8-1.0)
        # "buy", "best", "review", "price", etc.
        if self._has_commercial_intent(query_lower):
            return 0.95, None
        
        # Default: Informational queries (0.7-0.85)
        # General questions, how-to queries, etc.
        return 0.75, None
    
    def _is_sensitive(self, query: str) -> bool:
        """
        Check if query contains sensitive topics.
        
        Sensitive topics include:
        - Financial distress: unemployment, bankruptcy, debt, eviction, foreclosure
        - Grief and loss: death, funeral, bereavement, losing loved ones
        - Mental health crises: depression, anxiety, panic attacks, suicidal thoughts
        - Medical emergencies: heart attack, stroke, severe injury, need urgent medical help
        - Domestic violence and abuse: physical/emotional abuse, seeking protection
        - Addiction: seeking rehab, substance abuse help, withdrawal
        - Legal troubles: arrests, criminal charges, lawsuits
        - Pregnancy complications: miscarriage, stillbirth, high-risk pregnancy
        
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
        - Purchase intent: buy, purchase, shop, order, looking for, shopping for
        - Research intent: best, top, review, compare, recommend, which is better
        - Price intent: price, cost, cheap, affordable, deal, discount, how much
        - Product evaluation: should i buy, worth buying, pros and cons, quality
        - Shopping context: store, online shopping, free shipping, in stock
        - Brand queries: brand, model, alternative, warranty, return policy
        
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
            # Financial distress - unemployment
            re.compile(r'\b(unemployed|unemployment|jobless|out of work)\b', re.IGNORECASE),
            re.compile(r'\b(fired|laid off|layoff|terminated|let go|lost (my|our) job)\b', re.IGNORECASE),
            re.compile(r'\b(can\'?t find (a |)job|struggling to find work)\b', re.IGNORECASE),
            
            # Financial distress - debt and bankruptcy
            re.compile(r'\b(bankruptcy|bankrupt|filing for bankruptcy|going bankrupt)\b', re.IGNORECASE),
            re.compile(r'\b(debt collector|collection agency|repossession|foreclosure)\b', re.IGNORECASE),
            re.compile(r'\b(can\'?t pay|behind on payments|overdue payments|defaulting on)\b', re.IGNORECASE),
            re.compile(r'\b(financial crisis|financial trouble|money problems|broke)\b', re.IGNORECASE),
            re.compile(r'\b(eviction|being evicted|losing (my|our) home)\b', re.IGNORECASE),
            
            # Grief and loss - death
            re.compile(r'\b(passed away|died|death|deceased|fatal|fatality)\b', re.IGNORECASE),
            re.compile(r'\b(funeral|burial|cremation|memorial service|wake)\b', re.IGNORECASE),
            re.compile(r'\b(grief|grieving|mourning|bereavement)\b', re.IGNORECASE),
            re.compile(r'\b(lost (my|our|a) (mom|dad|mother|father|parent|son|daughter|child|baby|husband|wife|spouse|partner|friend|pet))\b', re.IGNORECASE),
            re.compile(r'\b(widow|widower|orphan)\b', re.IGNORECASE),
            
            # Mental health crises - depression and anxiety
            re.compile(r'\b(depressed|depression|severely depressed|clinically depressed)\b', re.IGNORECASE),
            re.compile(r'\b(anxious|anxiety|severe anxiety|panic attack|panic disorder)\b', re.IGNORECASE),
            re.compile(r'\b(mental breakdown|nervous breakdown|mental health crisis)\b', re.IGNORECASE),
            re.compile(r'\b(suicidal thoughts|suicidal ideation|contemplating suicide)\b', re.IGNORECASE),
            
            # Mental health crises - distress signals
            re.compile(r'\b(can\'?t cope|can\'?t handle|overwhelmed|breaking down)\b', re.IGNORECASE),
            re.compile(r'\b(feeling hopeless|feel hopeless|losing hope|no hope)\b', re.IGNORECASE),
            re.compile(r'\b(want to die|wish (i|I) was dead|don\'?t want to live)\b', re.IGNORECASE),
            re.compile(r'\b(gonna die|about to die|ready to die)\b', re.IGNORECASE),
            re.compile(r'\b(having a breakdown|mental collapse|emotional crisis)\b', re.IGNORECASE),
            
            # Medical emergencies - acute conditions
            re.compile(r'\b(heart attack|cardiac arrest|myocardial infarction)\b', re.IGNORECASE),
            re.compile(r'\b(stroke|brain hemorrhage|aneurysm)\b', re.IGNORECASE),
            re.compile(r'\b(overdose|poisoning|toxic)\b', re.IGNORECASE),
            re.compile(r'\b(seizure|convulsion|epileptic)\b', re.IGNORECASE),
            re.compile(r'\b(choking|can\'?t breathe|difficulty breathing|respiratory distress)\b', re.IGNORECASE),
            re.compile(r'\b(severe bleeding|hemorrhaging|blood loss)\b', re.IGNORECASE),
            re.compile(r'\b(broken bone|fracture|severe injury|trauma)\b', re.IGNORECASE),
            
            # Medical emergencies - help seeking
            re.compile(r'\b(emergency room|ER|urgent care|911|call ambulance)\b', re.IGNORECASE),
            re.compile(r'\b(need|require|seeking|looking for)\s+((urgent|severe|serious|critical|immediate|emergency)\s+)?(medical|health|doctor|hospital|physician)\s+(help|care|assistance|attention|treatment)\b', re.IGNORECASE),
            re.compile(r'\b(medical|health)\s+(emergency|crisis|urgency)\b', re.IGNORECASE),
            re.compile(r'\b(i\'?m\s+)?(sick|ill|injured|hurt|in pain)\s+(and\s+)?(need|require|want)\s+(help|doctor|hospital|treatment|care)\b', re.IGNORECASE),
            
            # Domestic violence and abuse
            re.compile(r'\b(domestic violence|domestic abuse|being abused|abusive relationship)\b', re.IGNORECASE),
            re.compile(r'\b(physical abuse|emotional abuse|verbal abuse|sexual abuse)\b', re.IGNORECASE),
            re.compile(r'\b(restraining order|protection order|safe house|women\'?s shelter)\b', re.IGNORECASE),
            
            # Addiction and substance abuse (seeking help)
            re.compile(r'\b(addiction help|rehab|rehabilitation|detox|withdrawal)\b', re.IGNORECASE),
            re.compile(r'\b(alcoholic|alcohol abuse|drinking problem|substance abuse)\b', re.IGNORECASE),
            re.compile(r'\b(overdosed|overdosing|drug problem)\b', re.IGNORECASE),
            
            # Legal troubles
            re.compile(r'\b(arrested|going to jail|facing charges|criminal charges)\b', re.IGNORECASE),
            re.compile(r'\b(court case|lawsuit|being sued|legal trouble)\b', re.IGNORECASE),
            
            # Pregnancy complications and loss
            re.compile(r'\b(miscarriage|stillbirth|pregnancy loss|lost (the |my )baby)\b', re.IGNORECASE),
            re.compile(r'\b(pregnancy complications|high-risk pregnancy|ectopic pregnancy)\b', re.IGNORECASE),
        ]
        return patterns
    
    def _compile_commercial_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for commercial intent detection.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # Direct purchase intent - specific contexts only
            re.compile(r'\b(buy|purchase|shop|order|acquire)\b', re.IGNORECASE),
            re.compile(r'\b(where (can i|to) (buy|get|find|purchase|order))\b', re.IGNORECASE),
            re.compile(r'\b(want to (buy|get|purchase|order))\b', re.IGNORECASE),
            re.compile(r'\b(looking for)\s+(a |an |new |the |some |)?(laptop|phone|computer|car|shoes|headphones|watch|camera|tv|tablet|product|item)\b', re.IGNORECASE),
            re.compile(r'\b(need (to buy|to purchase|a new))\b', re.IGNORECASE),
            re.compile(r'\b(shopping for|in the market for)\b', re.IGNORECASE),
            re.compile(r'\b(need to get|want to get)\s+(new|a|an)\b', re.IGNORECASE),
            
            # Research and comparison intent
            re.compile(r'\b(best|top|leading|premier|highest rated)\b', re.IGNORECASE),
            re.compile(r'\b(review|reviews|rating|ratings|testimonial)\b', re.IGNORECASE),
            re.compile(r'\b(compare|comparison|versus|vs\.?|compared to)\b', re.IGNORECASE),
            re.compile(r'\b(which (is|are) better|better than)\b', re.IGNORECASE),
            re.compile(r'\b(recommend|recommendation|suggest|suggestion|advice)\b', re.IGNORECASE),
            
            # Price and value intent
            re.compile(r'\b(price|cost|pricing|priced)\b', re.IGNORECASE),
            re.compile(r'\b(cheap|cheapest|affordable|inexpensive|budget)\b', re.IGNORECASE),
            re.compile(r'\b(deal|deals|discount|discounts|sale|sales|coupon|promo)\b', re.IGNORECASE),
            re.compile(r'\b(how much|what\'?s the (price|cost))\b', re.IGNORECASE),
            re.compile(r'\b(worth (it|buying|the money|the price))\b', re.IGNORECASE),
            re.compile(r'\b(good (deal|value|price)|great price)\b', re.IGNORECASE),
            
            # Product evaluation
            re.compile(r'\b(should i (buy|get|purchase)|worth (buying|getting))\b', re.IGNORECASE),
            re.compile(r'\b(pros and cons|advantages and disadvantages)\b', re.IGNORECASE),
            re.compile(r'\b(quality|durability|reliable|reliability)\b', re.IGNORECASE),
            
            # Shopping context
            re.compile(r'\b(store|stores|shop|shops|retailer|retailers)\b', re.IGNORECASE),
            re.compile(r'\b(online shopping|e-commerce|ecommerce)\b', re.IGNORECASE),
            re.compile(r'\b(free shipping|delivery|shipping)\b', re.IGNORECASE),
            re.compile(r'\b(in stock|availability|available)\b', re.IGNORECASE),
            
            # Brand and product queries
            re.compile(r'\b(brand|brands|model|models|version)\b', re.IGNORECASE),
            re.compile(r'\b(alternative|alternatives|substitute|replacement)\b', re.IGNORECASE),
            re.compile(r'\b(warranty|guarantee|return policy)\b', re.IGNORECASE),
        ]
        return patterns

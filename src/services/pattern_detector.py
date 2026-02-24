"""Service for detecting user intent patterns from query sequences."""

import re
from datetime import datetime, timedelta
from typing import List, Optional
from src.api.models.profiles import InferredIntent, QueryHistoryItem
from src.services.pattern_rules import PatternRule, PatternStep
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class PatternDetector:
    """
    Service for detecting user intent patterns from query sequences.
    
    Applies configurable rules to identify patterns like:
    - Marathon planning (shoes → weather → hotels)
    - Vacation planning (trip → flights → hotels)
    - Shopping research (reviews → prices)
    """
    
    def __init__(self, rules: List[PatternRule]):
        """
        Initialize the pattern detector.
        
        Args:
            rules: List of pattern rules to apply
        """
        self.rules = sorted(rules, key=lambda r: r.priority)
        logger.info(f"PatternDetector initialized with {len(rules)} rules")
    
    async def detect_patterns(
        self,
        query_history: List[QueryHistoryItem],
        user_id: str
    ) -> List[InferredIntent]:
        """
        Detect intent patterns from user's query history.
        
        Args:
            query_history: User's recent queries
            user_id: User identifier
        
        Returns:
            List of detected intents with confidence scores
        """
        detected_intents = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            intent = await self._match_rule(rule, query_history, user_id)
            if intent:
                detected_intents.append(intent)
                logger.info(
                    f"Pattern detected for user {user_id}: {rule.name} "
                    f"(confidence={intent.confidence:.2f})"
                )
        
        return detected_intents
    
    async def _match_rule(
        self,
        rule: PatternRule,
        query_history: List[QueryHistoryItem],
        user_id: str
    ) -> Optional[InferredIntent]:
        """
        Check if a rule matches the query history.
        
        Args:
            rule: Pattern rule to match
            query_history: User's query history
            user_id: User identifier
        
        Returns:
            InferredIntent if pattern matches, None otherwise
        """
        # Filter queries within time window
        cutoff_time = datetime.utcnow() - timedelta(hours=rule.time_window_hours)
        recent_queries = [q for q in query_history if q.timestamp >= cutoff_time]
        
        if len(recent_queries) < len(rule.pattern):
            return None
        
        # Try to find matching sequence
        match_result = self._find_matching_sequence(rule, recent_queries)
        
        if match_result is None:
            return None
        
        matched_queries, confidence, metadata = match_result
        
        # Check confidence threshold
        if confidence < rule.confidence_threshold:
            return None
        
        # Create InferredIntent
        intent = InferredIntent(
            intent_type=rule.rule_id,
            confidence=confidence,
            evidence=[q.query for q in matched_queries],
            detected_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=rule.time_window_hours * 2),
            inferred_categories=rule.inferred_categories,
            metadata={
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                **metadata
            }
        )
        
        return intent
    
    def _find_matching_sequence(
        self,
        rule: PatternRule,
        queries: List[QueryHistoryItem]
    ) -> Optional[tuple[List[QueryHistoryItem], float, dict]]:
        """
        Find a matching sequence of queries for the rule pattern.
        
        Args:
            rule: Pattern rule
            queries: Recent queries to search
        
        Returns:
            Tuple of (matched_queries, confidence, metadata) or None
        """
        # Try to match pattern steps in order
        matched_queries = []
        step_locations = {}
        
        for step in rule.pattern:
            match_found = False
            
            # Search for a query matching this step
            for query in queries:
                # Skip if already matched
                if query in matched_queries:
                    continue
                
                # Check if query matches step
                if self._query_matches_step(query, step, step_locations):
                    matched_queries.append(query)
                    
                    # Store location for future step matching
                    if query.location:
                        step_locations[step.step] = query.location
                    
                    match_found = True
                    break
            
            if not match_found:
                return None
        
        # Calculate confidence based on:
        # 1. How well queries match keywords
        # 2. Time proximity (closer = higher confidence)
        # 3. Location consistency
        confidence = self._calculate_confidence(matched_queries, rule, step_locations)
        
        # Extract metadata
        metadata = {}
        if step_locations:
            metadata["locations"] = list(set(step_locations.values()))
            if len(metadata["locations"]) == 1:
                metadata["primary_location"] = metadata["locations"][0]
        
        return matched_queries, confidence, metadata
    
    def _query_matches_step(
        self,
        query: QueryHistoryItem,
        step: PatternStep,
        step_locations: dict[int, str]
    ) -> bool:
        """
        Check if a query matches a pattern step.
        
        Args:
            query: Query to check
            step: Pattern step to match
            step_locations: Locations from previous steps
        
        Returns:
            True if query matches step requirements
        """
        query_lower = query.query.lower()
        
        # Check keyword matches
        keyword_matches = sum(
            1 for keyword in step.keywords
            if keyword.lower() in query_lower
        )
        
        if keyword_matches < step.min_keyword_matches:
            return False
        
        # Check category matches if required
        if step.category_match:
            if not any(cat in query.categories for cat in step.category_match):
                return False
        
        # Check location requirement
        if step.requires_location and not query.location:
            return False
        
        # Check location consistency with previous step
        if step.location_must_match_step is not None:
            previous_location = step_locations.get(step.location_must_match_step)
            if previous_location and query.location:
                # Fuzzy location matching (e.g., "Boston" matches "Boston, MA")
                if not self._locations_match(query.location, previous_location):
                    return False
        
        return True
    
    def _locations_match(self, loc1: str, loc2: str) -> bool:
        """
        Check if two locations match (fuzzy matching).
        
        Args:
            loc1: First location
            loc2: Second location
        
        Returns:
            True if locations match
        """
        # Normalize locations
        loc1_parts = set(part.strip().lower() for part in loc1.split(","))
        loc2_parts = set(part.strip().lower() for part in loc2.split(","))
        
        # Check if any parts overlap
        return bool(loc1_parts & loc2_parts)
    
    def _calculate_confidence(
        self,
        matched_queries: List[QueryHistoryItem],
        rule: PatternRule,
        step_locations: dict[int, str]
    ) -> float:
        """
        Calculate confidence score for a matched pattern.
        
        Args:
            matched_queries: Queries that matched the pattern
            rule: Pattern rule
            step_locations: Locations from matched steps
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence starts at 0.5
        confidence = 0.5
        
        # Boost for complete pattern match
        if len(matched_queries) == len(rule.pattern):
            confidence += 0.2
        
        # Boost for time proximity (queries close together = higher confidence)
        if len(matched_queries) >= 2:
            time_span = (matched_queries[-1].timestamp - matched_queries[0].timestamp).total_seconds()
            max_span = rule.time_window_hours * 3600
            
            # Closer queries = higher confidence
            time_proximity_score = 1.0 - (time_span / max_span)
            confidence += 0.2 * time_proximity_score
        
        # Boost for location consistency
        if len(step_locations) > 1:
            unique_locations = len(set(step_locations.values()))
            if unique_locations == 1:
                confidence += 0.1  # All same location
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """
        Extract location from query text.
        
        Args:
            query: Query text
        
        Returns:
            Extracted location or None
        """
        # Simple pattern matching for common location formats
        # e.g., "in Boston", "Boston weather", "hotels in New York"
        
        # Pattern: "in [Location]"
        match = re.search(r'\bin\s+([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})?)', query)
        if match:
            return match.group(1).strip()
        
        # Pattern: "[Location] weather/hotels/etc"
        match = re.search(r'([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})?)\s+(weather|hotel|flight)', query)
        if match:
            return match.group(1).strip()
        
        return None

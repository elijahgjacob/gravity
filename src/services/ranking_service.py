"""
SERVICE: Business logic for relevance ranking.

This service combines semantic similarity with context-based signals
to rank campaigns by relevance to the user's query and context.
"""

from typing import List, Optional


class RankingService:
    """
    SERVICE: Business logic for relevance ranking.
    
    Combines multiple signals to rank campaigns:
    - Semantic similarity (from vector search)
    - Category matching (exact and subcategory)
    - Context-based targeting (age, gender, location, interests)
    
    Performance: ~10-20ms for 1000 campaigns
    """
    
    def __init__(self):
        """Initialize the ranking service."""
        pass
    
    async def rank(
        self, 
        campaigns: List[dict], 
        query: str, 
        categories: List[str],
        context: Optional[dict] = None
    ) -> List[dict]:
        """
        Rank campaigns by relevance.
        
        Combines multiple ranking signals:
        1. Base semantic similarity score (from vector search)
        2. Category matching boosts (1.3x for exact, 1.15x for subcategory)
        3. Context-based targeting boosts (age, gender, location, interests)
        
        Args:
            campaigns: List of campaigns with similarity_score from search
            query: The user's query text
            categories: Extracted categories from CategoryService
            context: Optional user context (age, gender, location, interests)
        
        Returns:
            Sorted list of campaigns with added 'relevance_score' field
            (sorted by relevance_score descending)
        """
        # Calculate relevance scores for all campaigns
        for campaign in campaigns:
            # Start with base semantic similarity score
            score = campaign.get('similarity_score', 0.0)
            
            # Apply category matching boosts
            score = self._apply_category_boosts(campaign, categories, score)
            
            # Apply context-based targeting boosts
            if context:
                score = self._apply_context_boosts(campaign, context, score)
            
            # Normalize to 0-1 range (scores can exceed 1.0 with boosts)
            campaign['relevance_score'] = min(score, 1.0)
        
        # Sort by relevance score (descending - highest first)
        campaigns.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return campaigns
    
    def _apply_category_boosts(
        self, 
        campaign: dict, 
        categories: List[str], 
        base_score: float
    ) -> float:
        """
        Apply category matching boosts.
        
        Args:
            campaign: Campaign dictionary with category and subcategories
            categories: Extracted categories from query
            base_score: Base similarity score
        
        Returns:
            Boosted score
        """
        score = base_score
        
        # Boost if campaign's primary category matches extracted categories
        campaign_category = campaign.get('category', '')
        if campaign_category in categories:
            score *= 1.3  # 30% boost for exact category match
        
        # Boost for subcategory matches
        campaign_subcategories = campaign.get('subcategories', [])
        if any(subcat in categories for subcat in campaign_subcategories):
            score *= 1.15  # 15% boost for subcategory match
        
        return score
    
    def _apply_context_boosts(
        self, 
        campaign: dict, 
        context: dict, 
        base_score: float
    ) -> float:
        """
        Apply context-based targeting boosts.
        
        Boosts campaigns that match user demographics and interests:
        - Age targeting: 1.1x if user age in campaign's target range
        - Gender targeting: 1.05x if user gender matches
        - Location targeting: 1.15x if user location matches
        - Interest alignment: 1.0 + (0.1 * overlap_count)
        
        Args:
            campaign: Campaign dictionary with targeting field
            context: User context (age, gender, location, interests)
            base_score: Base score to boost
        
        Returns:
            Boosted score
        """
        score = base_score
        targeting = campaign.get('targeting', {})
        
        # Age targeting boost
        if context.get('age') and targeting.get('age_min') and targeting.get('age_max'):
            age = context['age']
            if targeting['age_min'] <= age <= targeting['age_max']:
                score *= 1.1  # 10% boost for age match
        
        # Gender targeting boost
        if context.get('gender') and targeting.get('genders'):
            if context['gender'] in targeting['genders']:
                score *= 1.05  # 5% boost for gender match
        
        # Location targeting boost
        if context.get('location') and targeting.get('locations'):
            # Simple country/state matching
            # e.g., "San Francisco, CA" -> ["San Francisco", "CA"]
            location_parts = context['location'].split(',')
            if any(loc.strip() in targeting['locations'] for loc in location_parts):
                score *= 1.15  # 15% boost for location match
        
        # Interest alignment boost
        if context.get('interests') and targeting.get('interests'):
            # Count overlapping interests
            user_interests = set(context['interests'])
            campaign_interests = set(targeting['interests'])
            interest_overlap = len(user_interests & campaign_interests)
            
            # 10% boost per overlapping interest
            score *= (1.0 + 0.1 * interest_overlap)
        
        return score

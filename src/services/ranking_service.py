"""
SERVICE: Business logic for relevance ranking.

This service combines semantic similarity with context-based signals
to rank campaigns by relevance to the user's query and context.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.intent_evolution_service import IntentEvolutionService


class RankingService:
    """
    SERVICE: Business logic for relevance ranking.
    
    Combines multiple signals to rank campaigns:
    - Semantic similarity (from vector search)
    - Category matching (exact and subcategory)
    - Context-based targeting (age, gender, location, interests)
    - Intent-based ranking (purchase readiness and ad strategy)
    
    Performance: ~10-20ms for 1000 campaigns
    """
    
    def __init__(self, intent_evolution_service: Optional['IntentEvolutionService'] = None):
        """
        Initialize the ranking service.
        
        Args:
            intent_evolution_service: Optional service for intent-based ranking
        """
        self.intent_evolution_service = intent_evolution_service
    
    async def rank(
        self, 
        campaigns: List[dict], 
        query: str, 
        categories: List[str],
        context: Optional[dict] = None,
        session_id: Optional[str] = None
    ) -> List[dict]:
        """
        Rank campaigns by relevance.
        
        Combines multiple ranking signals:
        1. Base semantic similarity score (from vector search)
        2. Category matching boosts (1.3x for exact, 1.15x for subcategory)
        3. Context-based targeting boosts (age, gender, location, interests)
        4. Intent-based ranking adjustments (purchase readiness and strategy)
        
        Args:
            campaigns: List of campaigns with similarity_score from search
            query: The user's query text
            categories: Extracted categories from CategoryService
            context: Optional user context (age, gender, location, interests)
            session_id: Optional session ID for intent-based ranking
        
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
        
        # Apply intent-based ranking adjustments
        if session_id and self.intent_evolution_service:
            campaigns = await self._apply_intent_based_ranking(campaigns, session_id)
        
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
    
    async def _apply_intent_based_ranking(
        self,
        campaigns: List[dict],
        session_id: str
    ) -> List[dict]:
        """
        Adjust campaign ranking based on purchase readiness and intent stage.
        
        Uses IntentEvolutionService to analyze session intent and boost
        campaigns that align with the user's current stage:
        - High readiness (0.8+): Boost conversion campaigns
        - Medium readiness (0.4-0.8): Boost comparison campaigns
        - Low readiness (0.0-0.4): Boost educational campaigns
        
        Args:
            campaigns: List of campaigns with relevance_score
            session_id: Session identifier
        
        Returns:
            Campaigns with adjusted relevance scores
        """
        try:
            # Get purchase readiness from intent evolution service
            readiness = await self.intent_evolution_service.calculate_purchase_readiness(
                session_id
            )
            
            # Apply intent-based boosts
            for campaign in campaigns:
                # High readiness (0.8+) → Boost conversion campaigns
                if readiness > 0.8:
                    if self._is_conversion_campaign(campaign):
                        campaign['relevance_score'] *= 1.3
                
                # Low readiness (0.0-0.4) → Boost educational campaigns
                elif readiness < 0.4:
                    if self._is_educational_campaign(campaign):
                        campaign['relevance_score'] *= 1.2
                
                # Medium readiness (0.4-0.8) → Boost comparison campaigns
                else:
                    if self._is_comparison_campaign(campaign):
                        campaign['relevance_score'] *= 1.25
                
                # Normalize to 0-1 range
                campaign['relevance_score'] = min(campaign['relevance_score'], 1.0)
            
            return campaigns
            
        except Exception as e:
            # Gracefully degrade if intent analysis fails
            # Just return campaigns unchanged
            return campaigns
    
    def _is_conversion_campaign(self, campaign: dict) -> bool:
        """
        Check if campaign is conversion-focused.
        
        Conversion campaigns have:
        - "buy", "purchase", "deal", "sale" in title/description
        - High CTA emphasis
        - Direct product links
        
        Args:
            campaign: Campaign dictionary
        
        Returns:
            True if conversion-focused
        """
        conversion_keywords = ['buy', 'purchase', 'deal', 'sale', 'discount', 
                               'offer', 'limited time', 'shop now', 'order']
        
        title = campaign.get('title', '').lower()
        description = campaign.get('description', '').lower()
        
        return any(keyword in title or keyword in description 
                   for keyword in conversion_keywords)
    
    def _is_educational_campaign(self, campaign: dict) -> bool:
        """
        Check if campaign is educational.
        
        Educational campaigns have:
        - "guide", "how to", "learn", "tips" in title/description
        - Informational content focus
        - No strong CTAs
        
        Args:
            campaign: Campaign dictionary
        
        Returns:
            True if educational
        """
        educational_keywords = ['guide', 'how to', 'learn', 'tips', 'tutorial',
                                'introduction', 'beginner', 'explained', 'what is']
        
        title = campaign.get('title', '').lower()
        description = campaign.get('description', '').lower()
        
        return any(keyword in title or keyword in description 
                   for keyword in educational_keywords)
    
    def _is_comparison_campaign(self, campaign: dict) -> bool:
        """
        Check if campaign is comparison-focused.
        
        Comparison campaigns have:
        - "vs", "compare", "review", "best" in title/description
        - Feature comparisons
        - Rating/review emphasis
        
        Args:
            campaign: Campaign dictionary
        
        Returns:
            True if comparison-focused
        """
        comparison_keywords = ['vs', 'versus', 'compare', 'comparison', 'review',
                               'best', 'top', 'rating', 'alternatives', 'options']
        
        title = campaign.get('title', '').lower()
        description = campaign.get('description', '').lower()
        
        return any(keyword in title or keyword in description 
                   for keyword in comparison_keywords)

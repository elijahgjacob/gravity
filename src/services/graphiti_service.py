"""Service for Graphiti knowledge graph event recording."""

from datetime import datetime
from typing import Dict, List, Optional
from src.repositories.graphiti_repository import GraphitiRepository
from src.api.models.events import QueryEvent, CampaignImpression, GraphitiEpisode
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GraphitiService:
    """
    Service for recording query events to Graphiti knowledge graph.
    
    Implements fire-and-forget pattern for async event recording
    without impacting retrieval latency.
    """
    
    def __init__(self, repository: GraphitiRepository):
        """
        Initialize the Graphiti service.
        
        Args:
            repository: GraphitiRepository instance
        """
        self.repository = repository
    
    async def record_query_event(
        self,
        query: str,
        context: Optional[Dict],
        eligibility: float,
        categories: List[str],
        campaigns: List[Dict],
        session_id: Optional[str] = None
    ) -> None:
        """
        Record a query event to the knowledge graph.
        
        This method builds a structured episode from the query event
        and adds it to Graphiti asynchronously.
        
        Args:
            query: User query text
            context: User context (age, gender, location, interests)
            eligibility: Ad eligibility score (0.0-1.0)
            categories: Extracted categories
            campaigns: Top campaigns shown (max 10)
            session_id: Optional session identifier
        
        Raises:
            Exception: If event recording fails
        """
        try:
            logger.debug(f"Recording query event: '{query[:50]}...'")
            
            # Build episode from query event
            episode_body = self._build_episode(
                query=query,
                context=context,
                eligibility=eligibility,
                categories=categories,
                campaigns=campaigns
            )
            
            # Generate unique episode name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            episode_name = f"query_{timestamp}"
            if session_id:
                episode_name = f"{episode_name}_{session_id}"
            
            # Add episode to Graphiti
            await self.repository.add_episode(
                name=episode_name,
                episode_body=episode_body,
                source_description="Ad Retrieval Query",
                reference_time=datetime.utcnow()
            )
            
            logger.debug(f"Query event recorded successfully: {episode_name}")
            
        except Exception as e:
            logger.error(f"Failed to record query event: {e}")
            raise
    
    def _build_episode(
        self,
        query: str,
        context: Optional[Dict],
        eligibility: float,
        categories: List[str],
        campaigns: List[Dict]
    ) -> str:
        """
        Build episode text from query event data.
        
        Creates a natural language description of the query event
        for Graphiti's LLM-based entity extraction.
        
        Args:
            query: User query text
            context: User context
            eligibility: Ad eligibility score
            categories: Extracted categories
            campaigns: Top campaigns shown
        
        Returns:
            Episode text content
        """
        # Start with query
        episode_parts = [f"User Query: \"{query}\""]
        
        # Add context if available
        if context:
            context_parts = []
            if "age" in context:
                context_parts.append(f"{context['age']} years old")
            if "gender" in context:
                context_parts.append(context["gender"])
            if "location" in context:
                context_parts.append(f"from {context['location']}")
            if "interests" in context and context["interests"]:
                interests_str = ", ".join(context["interests"])
                context_parts.append(f"interested in {interests_str}")
            
            if context_parts:
                episode_parts.append(f"User Context: {', '.join(context_parts)}")
        
        # Add eligibility score
        eligibility_desc = "highly appropriate" if eligibility >= 0.8 else \
                          "moderately appropriate" if eligibility >= 0.5 else \
                          "not appropriate"
        episode_parts.append(
            f"Ad Eligibility: {eligibility:.2f} ({eligibility_desc} for ads)"
        )
        
        # Add extracted categories
        if categories:
            categories_str = ", ".join(categories)
            episode_parts.append(f"Extracted Categories: {categories_str}")
        
        # Add top campaigns (only first 3 for brevity)
        if campaigns:
            episode_parts.append(f"Top {len(campaigns)} campaigns shown:")
            for i, campaign in enumerate(campaigns[:3], 1):
                campaign_desc = (
                    f"{i}. {campaign.get('title', campaign.get('campaign_id', 'Unknown'))} "
                    f"(category: {campaign.get('category', 'unknown')}, "
                    f"relevance: {campaign.get('relevance_score', 0):.2f})"
                )
                episode_parts.append(campaign_desc)
            
            if len(campaigns) > 3:
                episode_parts.append(f"... and {len(campaigns) - 3} more campaigns")
        
        # Join all parts
        episode_body = "\n".join(episode_parts)
        
        return episode_body
    
    async def record_campaign_click(
        self,
        query: str,
        campaign_id: str,
        campaign_title: str,
        position: int,
        session_id: Optional[str] = None
    ) -> None:
        """
        Record a campaign click event.
        
        Args:
            query: Original query
            campaign_id: Campaign that was clicked
            campaign_title: Campaign title
            position: Position in results
            session_id: Optional session identifier
        
        Raises:
            Exception: If event recording fails
        """
        try:
            logger.debug(f"Recording campaign click: {campaign_id}")
            
            episode_body = (
                f"User clicked on campaign: \"{campaign_title}\" (ID: {campaign_id})\n"
                f"Original query: \"{query}\"\n"
                f"Position in results: {position}"
            )
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            episode_name = f"click_{timestamp}_{campaign_id}"
            if session_id:
                episode_name = f"{episode_name}_{session_id}"
            
            await self.repository.add_episode(
                name=episode_name,
                episode_body=episode_body,
                source_description="Campaign Click",
                reference_time=datetime.utcnow()
            )
            
            logger.debug(f"Campaign click recorded: {episode_name}")
            
        except Exception as e:
            logger.error(f"Failed to record campaign click: {e}")
            raise

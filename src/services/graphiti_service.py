"""Service for Graphiti knowledge graph event recording."""

from datetime import datetime, timedelta
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
    
    async def record_conversational_query(
        self,
        query: str,
        session_id: str,
        previous_queries: List[Dict],
        context: Optional[Dict],
        eligibility: float,
        categories: List[str],
        campaigns: List[Dict]
    ) -> None:
        """
        Record query with full conversational context for LLM analysis.
        
        This enhanced recording includes session history and conversation dynamics,
        enabling Graphiti's LLM to extract intent signals, progression patterns,
        and purchase readiness indicators.
        
        Args:
            query: Current query text
            session_id: Session identifier
            previous_queries: List of previous queries in session (last 3-5)
            context: User context dictionary
            eligibility: Ad eligibility score
            categories: Extracted categories
            campaigns: Top campaigns (should be limited to 5-10)
        """
        episode_body = f"""
Session: {session_id}
Current Query: "{query}"

Conversation History:
{self._format_query_history(previous_queries)}

User Profile: {self._format_context(context)}
Ad Eligibility: {eligibility:.2f}
Categories: {', '.join(categories) if categories else 'None'}
Top Campaigns: {self._format_campaigns(campaigns[:5])}

Conversation Dynamics:
- Query count in session: {len(previous_queries) + 1}
- Time span: {self._calculate_time_span(previous_queries)}
- Topic evolution: {self._detect_topic_shift(previous_queries, query)}
- Timestamp: {datetime.now().isoformat()}
"""
        
        episode = GraphitiEpisode(
            name=f"conversational_query_{session_id}_{len(previous_queries) + 1}",
            episode_body=episode_body,
            source_description=f"Conversational query tracking for session {session_id}"
        )
        
        try:
            await self.repository.add_episode(
                name=episode.name,
                episode_body=episode.episode_body,
                source_description=episode.source_description,
                reference_time=datetime.utcnow()
            )
            logger.info(
                f"Recorded conversational query for session {session_id}: "
                f"query #{len(previous_queries) + 1}"
            )
        except Exception as e:
            logger.warning(f"Failed to record conversational query: {e}")
    
    def _format_query_history(self, previous_queries: List[Dict]) -> str:
        """Format previous queries for episode body."""
        if not previous_queries:
            return "No previous queries in session"
        
        # Limit to last 5 queries for context
        recent_queries = previous_queries[-5:]
        
        history_lines = []
        for i, q in enumerate(recent_queries, 1):
            timestamp = q.get('timestamp', 'Unknown time')
            query_text = q.get('query', 'Unknown query')
            eligibility = q.get('eligibility', 'N/A')
            
            history_lines.append(
                f"  {i}. [{timestamp}] \"{query_text}\" (eligibility: {eligibility})"
            )
        
        return "\n".join(history_lines)
    
    def _format_context(self, context: Optional[Dict]) -> str:
        """Format user context for episode body."""
        if not context:
            return "No user context provided"
        
        context_parts = []
        if "age" in context:
            context_parts.append(f"Age: {context['age']}")
        if "gender" in context:
            context_parts.append(f"Gender: {context['gender']}")
        if "location" in context:
            context_parts.append(f"Location: {context['location']}")
        if "interests" in context and context["interests"]:
            context_parts.append(f"Interests: {', '.join(context['interests'])}")
        
        return ", ".join(context_parts) if context_parts else "No context details"
    
    def _format_campaigns(self, campaigns: List[Dict]) -> str:
        """Format campaigns for episode body."""
        if not campaigns:
            return "No campaigns shown"
        
        campaign_lines = []
        for i, campaign in enumerate(campaigns, 1):
            title = campaign.get('title', campaign.get('campaign_id', 'Unknown'))
            category = campaign.get('category', 'unknown')
            relevance = campaign.get('relevance_score', 0)
            
            campaign_lines.append(
                f"  {i}. {title} (category: {category}, relevance: {relevance:.2f})"
            )
        
        return "\n".join(campaign_lines)
    
    def _calculate_time_span(self, previous_queries: List[Dict]) -> str:
        """Calculate time span of conversation."""
        if not previous_queries:
            return "New session"
        
        try:
            first_query = previous_queries[0]
            last_query = previous_queries[-1]
            
            first_time = first_query.get('timestamp')
            last_time = last_query.get('timestamp')
            
            if isinstance(first_time, datetime) and isinstance(last_time, datetime):
                duration = last_time - first_time
                
                if duration.total_seconds() < 60:
                    return f"{int(duration.total_seconds())} seconds"
                elif duration.total_seconds() < 3600:
                    return f"{int(duration.total_seconds() / 60)} minutes"
                else:
                    return f"{duration.total_seconds() / 3600:.1f} hours"
            
            return "Unknown duration"
        except Exception:
            return "Unknown duration"
    
    def _detect_topic_shift(self, previous_queries: List[Dict], current_query: str) -> str:
        """Detect if topic has shifted in conversation."""
        if not previous_queries:
            return "Initial query"
        
        try:
            last_query = previous_queries[-1].get('query', '')
            
            # Simple keyword overlap detection
            current_words = set(current_query.lower().split())
            last_words = set(last_query.lower().split())
            
            # Remove common stop words
            stop_words = {'i', 'a', 'the', 'is', 'are', 'for', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of'}
            current_words -= stop_words
            last_words -= stop_words
            
            if not current_words or not last_words:
                return "Continuing conversation"
            
            overlap = len(current_words & last_words) / len(current_words | last_words)
            
            if overlap > 0.5:
                return "Continuing same topic"
            elif overlap > 0.2:
                return "Related topic"
            else:
                return "New topic"
        except Exception:
            return "Unknown"

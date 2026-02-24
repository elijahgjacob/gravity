"""Repository for Graphiti knowledge graph operations."""

from datetime import datetime
from typing import Dict, List, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GraphitiRepository:
    """
    Repository for managing Graphiti knowledge graph operations.
    
    Handles Neo4j connection, episode creation, and graph queries.
    Uses OpenRouter for LLM-based entity extraction and relationship building.
    """
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openrouter_api_key: str,
        llm_model: str,
        namespace: str = "ad_retrieval"
    ):
        """
        Initialize the Graphiti repository.
        
        Args:
            neo4j_uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            openrouter_api_key: OpenRouter API key for LLM calls
            llm_model: OpenRouter model to use (e.g., anthropic/claude-3.5-sonnet)
            namespace: Graphiti namespace for data isolation
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.openrouter_api_key = openrouter_api_key
        self.llm_model = llm_model
        self.namespace = namespace
        
        self._graphiti_client = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize the Graphiti client with OpenRouter LLM configuration.
        
        Raises:
            ImportError: If graphiti-core is not installed
            Exception: If initialization fails
        """
        try:
            # Import Graphiti (lazy import to allow graceful degradation)
            from graphiti_core import Graphiti
            from graphiti_core.llm_client import OpenAIClient
            
            logger.info(f"Initializing Graphiti with OpenRouter model: {self.llm_model}")
            
            # Configure OpenRouter as LLM provider
            llm_client = OpenAIClient(
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                model=self.llm_model
            )
            
            # Initialize Graphiti client
            self._graphiti_client = Graphiti(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                llm_client=llm_client
            )
            
            self._initialized = True
            logger.info("Graphiti repository initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import Graphiti: {e}")
            raise ImportError(
                "graphiti-core is not installed. Run: pip install graphiti-core"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise
    
    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source_description: str = "Ad Retrieval Query",
        reference_time: Optional[datetime] = None
    ) -> None:
        """
        Add an episode to the knowledge graph.
        
        Args:
            name: Unique episode name
            episode_body: Episode text content
            source_description: Source of the episode
            reference_time: Reference time for temporal graph
        
        Raises:
            RuntimeError: If repository is not initialized
            Exception: If episode creation fails
        """
        if not self._initialized or self._graphiti_client is None:
            raise RuntimeError("Graphiti repository not initialized")
        
        try:
            if reference_time is None:
                reference_time = datetime.utcnow()
            
            logger.debug(f"Adding episode to Graphiti: {name}")
            
            await self._graphiti_client.add_episode(
                name=name,
                episode_body=episode_body,
                source_description=source_description,
                reference_time=reference_time
            )
            
            logger.debug(f"Episode added successfully: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add episode {name}: {e}")
            raise
    
    async def get_user_journey(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve user's query history from the knowledge graph.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of queries to return
        
        Returns:
            List of query events
        
        Raises:
            RuntimeError: If repository is not initialized
        """
        if not self._initialized or self._graphiti_client is None:
            raise RuntimeError("Graphiti repository not initialized")
        
        try:
            logger.debug(f"Retrieving user journey (user_id={user_id}, session_id={session_id})")
            
            # Query Graphiti for user journey
            # This is a placeholder - actual implementation depends on Graphiti's query API
            query = f"""
            MATCH (e:Episode)
            WHERE e.source = 'Ad Retrieval Query'
            """
            
            if user_id:
                query += f" AND e.user_id = '{user_id}'"
            if session_id:
                query += f" AND e.session_id = '{session_id}'"
            
            query += f"""
            RETURN e
            ORDER BY e.timestamp DESC
            LIMIT {limit}
            """
            
            # Execute query (placeholder - actual implementation may differ)
            results = []
            logger.debug(f"Retrieved {len(results)} query events")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve user journey: {e}")
            raise
    
    async def get_campaign_relationships(
        self,
        campaign_id: str,
        relationship_type: str = "co_occurrence",
        limit: int = 10
    ) -> List[Dict]:
        """
        Query campaign co-occurrence patterns from the knowledge graph.
        
        Args:
            campaign_id: Campaign identifier
            relationship_type: Type of relationship to query
            limit: Maximum number of related campaigns to return
        
        Returns:
            List of related campaigns with relationship strength
        
        Raises:
            RuntimeError: If repository is not initialized
        """
        if not self._initialized or self._graphiti_client is None:
            raise RuntimeError("Graphiti repository not initialized")
        
        try:
            logger.debug(f"Retrieving campaign relationships for {campaign_id}")
            
            # Query Graphiti for campaign relationships
            # This is a placeholder - actual implementation depends on Graphiti's query API
            results = []
            logger.debug(f"Retrieved {len(results)} related campaigns")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve campaign relationships: {e}")
            raise
    
    async def shutdown(self):
        """
        Cleanup Graphiti client and Neo4j connections.
        """
        try:
            if self._graphiti_client is not None:
                logger.info("Shutting down Graphiti repository")
                # Close Neo4j driver if needed
                self._graphiti_client = None
                self._initialized = False
                logger.info("Graphiti repository shut down successfully")
        except Exception as e:
            logger.error(f"Error during Graphiti shutdown: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if repository is initialized."""
        return self._initialized

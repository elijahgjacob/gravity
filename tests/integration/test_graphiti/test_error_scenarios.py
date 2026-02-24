"""Integration tests for Graphiti error scenarios."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from src.services.graphiti_service import GraphitiService


class TestGraphitiErrorHandling:
    """Test error handling in Graphiti integration."""
    
    @pytest.mark.asyncio
    async def test_graphiti_neo4j_connection_error(self):
        """Test handling of Neo4j connection errors."""
        mock_repo = MagicMock()
        mock_repo.add_episode = AsyncMock(side_effect=Exception("Connection refused"))
        
        service = GraphitiService(repository=mock_repo)
        
        with pytest.raises(Exception) as exc_info:
            await service.record_query_event(
                query="test query",
                context=None,
                eligibility=0.95,
                categories=["test"],
                campaigns=[]
            )
        
        assert "Connection refused" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_graphiti_openrouter_api_error(self):
        """Test handling of OpenRouter API errors."""
        mock_repo = MagicMock()
        mock_repo.add_episode = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        
        service = GraphitiService(repository=mock_repo)
        
        with pytest.raises(Exception) as exc_info:
            await service.record_query_event(
                query="test query",
                context=None,
                eligibility=0.95,
                categories=["test"],
                campaigns=[]
            )
        
        assert "API rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_graphiti_timeout_error(self):
        """Test handling of timeout errors."""
        mock_repo = MagicMock()
        mock_repo.add_episode = AsyncMock(side_effect=TimeoutError("Request timeout"))
        
        service = GraphitiService(repository=mock_repo)
        
        with pytest.raises(TimeoutError):
            await service.record_query_event(
                query="test query",
                context=None,
                eligibility=0.95,
                categories=["test"],
                campaigns=[]
            )


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    def test_controller_works_without_graphiti_service(self):
        """Test that controller works when graphiti_service is None."""
        from src.controllers.retrieval_controller import RetrievalController
        from src.services.eligibility_service import EligibilityService
        from src.services.category_service import CategoryService
        from src.services.embedding_service import EmbeddingService
        from src.services.search_service import SearchService
        from src.services.ranking_service import RankingService
        from src.repositories.blocklist_repository import BlocklistRepository
        from src.repositories.taxonomy_repository import TaxonomyRepository
        from src.repositories.vector_repository import VectorRepository
        from src.repositories.campaign_repository import CampaignRepository
        from src.core.config import settings
        
        # Initialize without Graphiti
        blocklist_repo = BlocklistRepository(settings.BLOCKLIST_PATH)
        taxonomy_repo = TaxonomyRepository(settings.TAXONOMY_PATH)
        vector_repo = VectorRepository(settings.FAISS_INDEX_PATH)
        campaign_repo = CampaignRepository(settings.CAMPAIGNS_PATH)
        
        eligibility_service = EligibilityService(blocklist_repo)
        category_service = CategoryService(taxonomy_repo)
        embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
        search_service = SearchService(vector_repo, campaign_repo)
        ranking_service = RankingService()
        
        controller = RetrievalController(
            eligibility_service=eligibility_service,
            category_service=category_service,
            embedding_service=embedding_service,
            search_service=search_service,
            ranking_service=ranking_service,
            graphiti_service=None  # Explicitly None
        )
        
        assert controller.graphiti_service is None
        assert controller.eligibility_service is not None

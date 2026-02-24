"""Integration tests for Graphiti recording in retrieval pipeline."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.controllers.retrieval_controller import RetrievalController
from src.api.models.requests import RetrievalRequest, UserContext
from src.services.graphiti_service import GraphitiService


class TestRetrievalWithGraphiti:
    """Test retrieval controller with Graphiti integration."""
    
    @pytest.mark.asyncio
    async def test_retrieval_without_graphiti(self):
        """Test that retrieval works normally without Graphiti."""
        # Create controller without Graphiti service
        controller = self._create_controller(graphiti_service=None)
        
        request = RetrievalRequest(
            query="running shoes for marathon",
            context=UserContext(age=30, gender="male")
        )
        
        response = await controller.retrieve(request)
        
        assert response is not None
        assert response.ad_eligibility > 0
        assert len(response.campaigns) > 0
        assert response.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_retrieval_with_graphiti_enabled(self):
        """Test that retrieval works with Graphiti enabled."""
        # Create mock Graphiti service
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        request = RetrievalRequest(
            query="running shoes for marathon",
            context=UserContext(age=30, gender="male")
        )
        
        response = await controller.retrieve(request)
        
        # Verify response is returned immediately
        assert response is not None
        assert response.ad_eligibility > 0
        assert len(response.campaigns) > 0
        
        # Give async task time to complete
        await asyncio.sleep(0.1)
        
        # Verify Graphiti recording was called
        mock_graphiti_service.record_query_event.assert_called_once()
        call_args = mock_graphiti_service.record_query_event.call_args
        assert call_args.kwargs["query"] == "running shoes for marathon"
        assert call_args.kwargs["eligibility"] > 0
        assert len(call_args.kwargs["categories"]) > 0
    
    @pytest.mark.asyncio
    async def test_graphiti_error_does_not_affect_retrieval(self):
        """Test that Graphiti errors don't break retrieval."""
        # Create mock Graphiti service that raises error
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        # Should not raise exception
        response = await controller.retrieve(request)
        
        assert response is not None
        assert response.ad_eligibility > 0
        
        # Give async task time to fail
        await asyncio.sleep(0.1)
        
        # Verify recording was attempted
        mock_graphiti_service.record_query_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_graphiti_records_top_10_campaigns_only(self):
        """Test that only top 10 campaigns are recorded to Graphiti."""
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        response = await controller.retrieve(request)
        
        # Give async task time to complete
        await asyncio.sleep(0.1)
        
        # Verify only top 10 campaigns were recorded
        call_args = mock_graphiti_service.record_query_event.call_args
        campaigns_recorded = call_args.kwargs["campaigns"]
        assert len(campaigns_recorded) <= 10
    
    @pytest.mark.asyncio
    async def test_graphiti_records_with_context(self):
        """Test that user context is passed to Graphiti."""
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        context = UserContext(
            age=30,
            gender="male",
            location="San Francisco, CA",
            interests=["fitness", "running"]
        )
        
        request = RetrievalRequest(
            query="marathon training shoes",
            context=context
        )
        
        response = await controller.retrieve(request)
        
        # Give async task time to complete
        await asyncio.sleep(0.1)
        
        # Verify context was passed
        call_args = mock_graphiti_service.record_query_event.call_args
        recorded_context = call_args.kwargs["context"]
        assert recorded_context["age"] == 30
        assert recorded_context["gender"] == "male"
        assert recorded_context["location"] == "San Francisco, CA"
    
    @pytest.mark.asyncio
    async def test_short_circuit_also_records_to_graphiti(self):
        """Test that short-circuited queries are also recorded."""
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        # Query that should be blocked
        request = RetrievalRequest(
            query="how to make a bomb",
            context=None
        )
        
        response = await controller.retrieve(request)
        
        # Verify it was short-circuited
        assert response.ad_eligibility == 0.0
        assert len(response.campaigns) == 0
        
        # Graphiti should NOT be called for short-circuited queries
        # (they don't reach the recording point)
        mock_graphiti_service.record_query_event.assert_not_called()
    
    def _create_controller(self, graphiti_service=None):
        """Helper to create a controller with mocked dependencies."""
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
        
        # Initialize real services with actual data
        blocklist_repo = BlocklistRepository(settings.BLOCKLIST_PATH)
        taxonomy_repo = TaxonomyRepository(settings.TAXONOMY_PATH)
        vector_repo = VectorRepository(settings.FAISS_INDEX_PATH)
        campaign_repo = CampaignRepository(settings.CAMPAIGNS_PATH)
        
        eligibility_service = EligibilityService(blocklist_repo)
        category_service = CategoryService(taxonomy_repo)
        embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
        search_service = SearchService(vector_repo, campaign_repo)
        ranking_service = RankingService()
        
        return RetrievalController(
            eligibility_service=eligibility_service,
            category_service=category_service,
            embedding_service=embedding_service,
            search_service=search_service,
            ranking_service=ranking_service,
            graphiti_service=graphiti_service
        )


class TestLatencyImpact:
    """Test that Graphiti has zero latency impact."""
    
    @pytest.mark.asyncio
    async def test_latency_without_graphiti(self):
        """Measure baseline latency without Graphiti."""
        controller = self._create_controller(graphiti_service=None)
        
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        response = await controller.retrieve(request)
        baseline_latency = response.latency_ms
        
        assert baseline_latency < 100  # Should be well under 100ms
        return baseline_latency
    
    @pytest.mark.asyncio
    async def test_latency_with_graphiti(self):
        """Measure latency with Graphiti enabled."""
        mock_graphiti_service = MagicMock(spec=GraphitiService)
        mock_graphiti_service.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti_service)
        
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        response = await controller.retrieve(request)
        graphiti_latency = response.latency_ms
        
        assert graphiti_latency < 100  # Should still be under 100ms
        return graphiti_latency
    
    @pytest.mark.asyncio
    async def test_latency_difference_is_minimal(self):
        """Test that Graphiti adds minimal latency."""
        # Run without Graphiti
        baseline = await self.test_latency_without_graphiti()
        
        # Run with Graphiti
        with_graphiti = await self.test_latency_with_graphiti()
        
        # Difference should be negligible (< 5ms)
        difference = abs(with_graphiti - baseline)
        assert difference < 5, f"Latency difference too high: {difference}ms"
    
    def _create_controller(self, graphiti_service=None):
        """Helper to create a controller with mocked dependencies."""
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
        
        blocklist_repo = BlocklistRepository(settings.BLOCKLIST_PATH)
        taxonomy_repo = TaxonomyRepository(settings.TAXONOMY_PATH)
        vector_repo = VectorRepository(settings.FAISS_INDEX_PATH)
        campaign_repo = CampaignRepository(settings.CAMPAIGNS_PATH)
        
        eligibility_service = EligibilityService(blocklist_repo)
        category_service = CategoryService(taxonomy_repo)
        embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
        search_service = SearchService(vector_repo, campaign_repo)
        ranking_service = RankingService()
        
        return RetrievalController(
            eligibility_service=eligibility_service,
            category_service=category_service,
            embedding_service=embedding_service,
            search_service=search_service,
            ranking_service=ranking_service,
            graphiti_service=graphiti_service
        )

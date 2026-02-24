"""Tests to verify Graphiti has zero latency impact."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.controllers.retrieval_controller import RetrievalController
from src.api.models.requests import RetrievalRequest, UserContext
from src.services.graphiti_service import GraphitiService


class TestLatencyImpact:
    """Test that Graphiti recording has zero impact on retrieval latency."""
    
    @pytest.mark.asyncio
    async def test_baseline_latency(self):
        """Measure baseline latency without Graphiti."""
        controller = self._create_controller(graphiti_service=None)
        
        request = RetrievalRequest(
            query="running shoes for marathon training",
            context=UserContext(age=30, gender="male")
        )
        
        start = time.perf_counter()
        response = await controller.retrieve(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert response is not None
        assert elapsed_ms < 100  # Should be well under 100ms
        assert abs(elapsed_ms - response.latency_ms) < 5  # Should match response latency
    
    @pytest.mark.asyncio
    async def test_latency_with_graphiti_mock(self):
        """Test latency with mocked Graphiti service."""
        # Create fast mock that returns immediately
        mock_graphiti = MagicMock(spec=GraphitiService)
        mock_graphiti.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti)
        
        request = RetrievalRequest(
            query="running shoes for marathon training",
            context=UserContext(age=30, gender="male")
        )
        
        start = time.perf_counter()
        response = await controller.retrieve(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert response is not None
        assert elapsed_ms < 100
        
        # Latency should be essentially the same as baseline
        # (fire-and-forget adds <1ms overhead)
        assert elapsed_ms < 50  # Still very fast
    
    @pytest.mark.asyncio
    async def test_latency_with_slow_graphiti(self):
        """Test that slow Graphiti recording doesn't block response."""
        # Create slow mock that takes 500ms
        async def slow_record(*args, **kwargs):
            await asyncio.sleep(0.5)  # 500ms delay
        
        mock_graphiti = MagicMock(spec=GraphitiService)
        mock_graphiti.record_query_event = AsyncMock(side_effect=slow_record)
        
        controller = self._create_controller(graphiti_service=mock_graphiti)
        
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        start = time.perf_counter()
        response = await controller.retrieve(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Response should return immediately, not wait for Graphiti
        assert elapsed_ms < 100, f"Latency too high: {elapsed_ms}ms (Graphiti blocking?)"
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_multiple_requests_with_graphiti(self):
        """Test that multiple concurrent requests work with Graphiti."""
        import asyncio
        
        mock_graphiti = MagicMock(spec=GraphitiService)
        mock_graphiti.record_query_event = AsyncMock()
        
        controller = self._create_controller(graphiti_service=mock_graphiti)
        
        # Create 10 concurrent requests
        requests = [
            RetrievalRequest(query=f"query {i}", context=None)
            for i in range(10)
        ]
        
        start = time.perf_counter()
        responses = await asyncio.gather(*[
            controller.retrieve(req) for req in requests
        ])
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # All requests should complete
        assert len(responses) == 10
        
        # Average latency per request should still be low
        avg_latency = elapsed_ms / 10
        assert avg_latency < 100
    
    def _create_controller(self, graphiti_service=None):
        """Helper to create a controller with real dependencies."""
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

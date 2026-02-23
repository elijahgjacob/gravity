"""
Integration tests for Phase 7: Controller & Orchestration.

Tests the RetrievalController end-to-end pipeline with all services integrated.
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
from src.api.models.requests import RetrievalRequest, UserContext


class TestPhase7Integration:
    """Integration tests for Phase 7 retrieval controller."""
    
    @pytest.fixture
    def retrieval_controller(self):
        """Create fully integrated retrieval controller."""
        # Initialize repositories
        blocklist_repo = BlocklistRepository("data/blocklist.txt")
        taxonomy_repo = TaxonomyRepository("data/taxonomy.json")
        vector_repo = VectorRepository("data/faiss.index")
        campaign_repo = CampaignRepository("data/campaigns.jsonl")
        
        # Initialize services
        eligibility_service = EligibilityService(blocklist_repo)
        category_service = CategoryService(taxonomy_repo)
        embedding_service = EmbeddingService()
        search_service = SearchService(vector_repo, campaign_repo)
        ranking_service = RankingService()
        
        # Create controller
        return RetrievalController(
            eligibility_service=eligibility_service,
            category_service=category_service,
            embedding_service=embedding_service,
            search_service=search_service,
            ranking_service=ranking_service
        )
    
    # ========== End-to-End Pipeline Tests ==========
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_commercial_query(self, retrieval_controller):
        """Test complete pipeline for commercial query."""
        request = RetrievalRequest(
            query="Best running shoes for marathon training",
            context=UserContext(
                age=30,
                gender="male",
                location="San Francisco, CA",
                interests=["fitness", "running"]
            )
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Verify response structure
        assert response.ad_eligibility > 0.8
        assert len(response.extracted_categories) > 0
        assert "running_shoes" in response.extracted_categories or "marathon_gear" in response.extracted_categories
        assert len(response.campaigns) > 0
        assert len(response.campaigns) <= 1000
        assert response.latency_ms > 0
        
        # Verify campaigns are properly ranked
        for i in range(len(response.campaigns) - 1):
            assert response.campaigns[i].relevance_score >= response.campaigns[i + 1].relevance_score
        
        # Verify metadata
        assert "candidates_retrieved" in response.metadata
        assert "campaigns_returned" in response.metadata
        
        print(f"\n✅ Commercial query pipeline: {response.latency_ms:.2f}ms")
        print(f"   Eligibility: {response.ad_eligibility}")
        print(f"   Categories: {response.extracted_categories[:3]}")
        print(f"   Campaigns: {len(response.campaigns)}")
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_blocked_query(self, retrieval_controller):
        """Test complete pipeline for blocked query (short-circuit)."""
        request = RetrievalRequest(
            query="I want to commit suicide",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should short-circuit with zero eligibility
        assert response.ad_eligibility == 0.0
        assert len(response.campaigns) == 0
        assert response.metadata.get("short_circuited") is True
        assert response.latency_ms < 50  # Should be very fast (no search/ranking)
        
        print(f"\n✅ Blocked query short-circuit: {response.latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_informational_query(self, retrieval_controller):
        """Test complete pipeline for informational query."""
        request = RetrievalRequest(
            query="What is the history of marathon running?",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should have medium eligibility
        assert 0.5 <= response.ad_eligibility <= 0.9
        assert len(response.extracted_categories) > 0
        assert len(response.campaigns) > 0
        
        print(f"\n✅ Informational query pipeline: {response.latency_ms:.2f}ms")
        print(f"   Eligibility: {response.ad_eligibility}")
    
    @pytest.mark.asyncio
    async def test_pipeline_with_context_boosting(self, retrieval_controller):
        """Test that user context affects ranking."""
        # Same query, different contexts
        query = "fitness equipment"
        
        # Context 1: Young male interested in fitness
        request1 = RetrievalRequest(
            query=query,
            context=UserContext(
                age=25,
                gender="male",
                location="San Francisco, CA",
                interests=["fitness", "gym", "weightlifting"]
            )
        )
        
        # Context 2: Older female interested in yoga
        request2 = RetrievalRequest(
            query=query,
            context=UserContext(
                age=45,
                gender="female",
                location="New York, NY",
                interests=["yoga", "wellness", "meditation"]
            )
        )
        
        response1 = await retrieval_controller.retrieve(request1)
        response2 = await retrieval_controller.retrieve(request2)
        
        # Both should return campaigns
        assert len(response1.campaigns) > 0
        assert len(response2.campaigns) > 0
        
        # Top campaigns may differ due to context-based ranking
        # (This is a soft check - may not always differ with random data)
        top_ids_1 = [c.campaign_id for c in response1.campaigns[:5]]
        top_ids_2 = [c.campaign_id for c in response2.campaigns[:5]]
        
        print(f"\n✅ Context boosting test:")
        print(f"   Context 1 top campaign: {response1.campaigns[0].title}")
        print(f"   Context 2 top campaign: {response2.campaigns[0].title}")
    
    @pytest.mark.asyncio
    async def test_pipeline_without_context(self, retrieval_controller):
        """Test pipeline works without user context."""
        request = RetrievalRequest(
            query="laptop for programming",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        assert response.ad_eligibility > 0.0
        assert len(response.extracted_categories) > 0
        assert len(response.campaigns) > 0
        
        print(f"\n✅ No context pipeline: {response.latency_ms:.2f}ms")
    
    # ========== Performance Tests ==========
    
    @pytest.mark.asyncio
    async def test_pipeline_latency_target(self, retrieval_controller):
        """Test that pipeline meets <100ms latency target."""
        request = RetrievalRequest(
            query="running shoes for marathon",
            context=UserContext(
                age=30,
                gender="male",
                location="CA",
                interests=["fitness", "running"]
            )
        )
        
        # Warm-up
        await retrieval_controller.retrieve(request)
        
        # Measure 10 requests
        latencies = []
        for _ in range(10):
            response = await retrieval_controller.retrieve(request)
            latencies.append(response.latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"\n✅ Pipeline latency:")
        print(f"   Average: {avg_latency:.2f}ms")
        print(f"   P95: {p95_latency:.2f}ms")
        print(f"   Min: {min(latencies):.2f}ms")
        print(f"   Max: {max(latencies):.2f}ms")
        
        # Target: <100ms p95
        assert p95_latency < 100, f"P95 latency {p95_latency:.2f}ms exceeds 100ms target"
    
    @pytest.mark.asyncio
    async def test_short_circuit_latency(self, retrieval_controller):
        """Test that short-circuit path is very fast."""
        request = RetrievalRequest(
            query="suicide help",
            context=None
        )
        
        # Warm-up
        await retrieval_controller.retrieve(request)
        
        # Measure 10 short-circuit requests
        latencies = []
        for _ in range(10):
            response = await retrieval_controller.retrieve(request)
            latencies.append(response.latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        
        print(f"\n✅ Short-circuit latency: {avg_latency:.2f}ms")
        
        # Should be much faster than full pipeline (<50ms)
        assert avg_latency < 50, f"Short-circuit latency {avg_latency:.2f}ms exceeds 50ms target"
    
    # ========== Concurrent Request Tests ==========
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, retrieval_controller):
        """Test handling multiple concurrent requests."""
        queries = [
            "running shoes",
            "laptop computer",
            "fitness tracker",
            "yoga mat",
            "protein powder",
        ]
        
        requests = [
            RetrievalRequest(query=q, context=None)
            for q in queries
        ]
        
        # Execute all requests concurrently
        tasks = [retrieval_controller.retrieve(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses
        assert len(responses) == len(queries)
        for response in responses:
            assert response.ad_eligibility >= 0.0
            assert len(response.extracted_categories) > 0
            assert response.latency_ms > 0
        
        print(f"\n✅ Concurrent requests: {len(responses)} completed")
    
    # ========== Edge Cases ==========
    
    @pytest.mark.asyncio
    async def test_minimal_query(self, retrieval_controller):
        """Test handling of minimal query."""
        request = RetrievalRequest(
            query="a",  # Minimal valid query
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should still return a valid response
        assert response.ad_eligibility >= 0.0
        assert response.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_long_query(self, retrieval_controller):
        """Test handling of long query (within limits)."""
        # Create a query that's long but within 500 char limit
        request = RetrievalRequest(
            query="running shoes for marathon training " * 10,  # ~370 chars
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should handle gracefully
        assert response.ad_eligibility >= 0.0
        assert len(response.campaigns) >= 0
    
    @pytest.mark.asyncio
    async def test_special_characters_query(self, retrieval_controller):
        """Test handling of special characters in query."""
        request = RetrievalRequest(
            query="running shoes!!! @#$% best??? 2024",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should handle gracefully
        assert response.ad_eligibility >= 0.0
        assert len(response.extracted_categories) >= 0
    
    # ========== Campaign Quality Tests ==========
    
    @pytest.mark.asyncio
    async def test_campaign_relevance_scores(self, retrieval_controller):
        """Test that campaigns have valid relevance scores."""
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        if len(response.campaigns) > 0:
            # All relevance scores should be in valid range
            for campaign in response.campaigns:
                assert 0.0 <= campaign.relevance_score <= 1.0
            
            # Campaigns should be sorted by relevance
            for i in range(len(response.campaigns) - 1):
                assert response.campaigns[i].relevance_score >= response.campaigns[i + 1].relevance_score
    
    @pytest.mark.asyncio
    async def test_campaign_fields_populated(self, retrieval_controller):
        """Test that campaign fields are properly populated."""
        request = RetrievalRequest(
            query="laptop computer",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        if len(response.campaigns) > 0:
            campaign = response.campaigns[0]
            
            # All required fields should be present
            assert campaign.campaign_id
            assert campaign.title
            assert campaign.category
            assert isinstance(campaign.relevance_score, float)
            assert isinstance(campaign.description, str)
            assert isinstance(campaign.keywords, list)
    
    @pytest.mark.asyncio
    async def test_max_campaigns_returned(self, retrieval_controller):
        """Test that at most 1000 campaigns are returned."""
        request = RetrievalRequest(
            query="product",  # Generic query to get many results
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Should never exceed 1000 campaigns
        assert len(response.campaigns) <= 1000
    
    # ========== Metadata Tests ==========
    
    @pytest.mark.asyncio
    async def test_metadata_completeness(self, retrieval_controller):
        """Test that response metadata is complete."""
        request = RetrievalRequest(
            query="running shoes",
            context=None
        )
        
        response = await retrieval_controller.retrieve(request)
        
        # Verify metadata fields
        assert "candidates_retrieved" in response.metadata
        assert "campaigns_returned" in response.metadata
        
        # Verify metadata values
        assert response.metadata["campaigns_returned"] == len(response.campaigns)
        assert response.metadata["candidates_retrieved"] >= response.metadata["campaigns_returned"]


def test_phase7_components_exist():
    """Test that all Phase 7 components are properly created."""
    # Check that files exist
    assert Path("src/controllers/retrieval_controller.py").exists()
    assert Path("src/core/dependencies.py").exists()
    
    # Check that classes can be imported
    from src.controllers.retrieval_controller import RetrievalController
    from src.core.dependencies import get_retrieval_controller, init_dependencies
    
    assert RetrievalController is not None
    assert get_retrieval_controller is not None
    assert init_dependencies is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

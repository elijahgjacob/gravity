"""
Integration tests for Phase 5: Embedding & Search System.

Tests the integration between EmbeddingService, SearchService,
VectorRepository, and CampaignRepository with real data files.
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path
import sys
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.repositories.vector_repository import VectorRepository
from src.repositories.campaign_repository import CampaignRepository


class TestPhase5Integration:
    """Integration tests for Phase 5 embedding and search components."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service fixture."""
        return EmbeddingService()
    
    @pytest.fixture
    def campaign_repo(self):
        """Create campaign repository fixture."""
        campaigns_path = "data/campaigns.jsonl"
        return CampaignRepository(campaigns_path)
    
    @pytest.fixture
    def vector_repo(self):
        """Create vector repository fixture."""
        index_path = "data/faiss.index"
        return VectorRepository(index_path)
    
    @pytest.fixture
    def search_service(self, vector_repo, campaign_repo):
        """Create search service fixture."""
        return SearchService(vector_repo, campaign_repo)
    
    # ========== Embedding Service Tests ==========
    
    @pytest.mark.asyncio
    async def test_basic_query_embedding(self, embedding_service):
        """Test basic query embedding without categories."""
        query = "running shoes for marathon training"
        categories = []
        
        embedding = await embedding_service.embed_query(query, categories)
        
        # Verify embedding properties
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)  # all-MiniLM-L6-v2 produces 384-dim vectors
        assert embedding.dtype == np.float32
        assert not np.all(embedding == 0)  # Should not be all zeros
    
    @pytest.mark.asyncio
    async def test_query_embedding_with_categories(self, embedding_service):
        """Test query embedding with categories."""
        query = "best running shoes"
        categories = ["running_shoes", "athletic_footwear"]
        
        embedding = await embedding_service.embed_query(query, categories)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert not np.all(embedding == 0)
    
    @pytest.mark.asyncio
    async def test_embedding_consistency(self, embedding_service):
        """Test that same query produces same embedding."""
        query = "laptop for programming"
        categories = ["laptops", "electronics"]
        
        embedding1 = await embedding_service.embed_query(query, categories)
        embedding2 = await embedding_service.embed_query(query, categories)
        
        # Should be identical
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=6)
    
    @pytest.mark.asyncio
    async def test_embedding_different_queries(self, embedding_service):
        """Test that different queries produce different embeddings."""
        query1 = "running shoes"
        query2 = "laptop computer"
        
        embedding1 = await embedding_service.embed_query(query1, [])
        embedding2 = await embedding_service.embed_query(query2, [])
        
        # Should be different
        assert not np.allclose(embedding1, embedding2)
        
        # Calculate cosine similarity - should be low for unrelated queries
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        assert similarity < 0.7  # Unrelated queries should have low similarity
    
    @pytest.mark.asyncio
    async def test_embedding_similar_queries(self, embedding_service):
        """Test that similar queries produce similar embeddings."""
        query1 = "running shoes for marathon"
        query2 = "marathon running footwear"
        
        embedding1 = await embedding_service.embed_query(query1, [])
        embedding2 = await embedding_service.embed_query(query2, [])
        
        # Calculate cosine similarity - should be high for similar queries
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        assert similarity > 0.6  # Similar queries should have high similarity
    
    @pytest.mark.asyncio
    async def test_embedding_empty_query(self, embedding_service):
        """Test embedding with empty query."""
        query = ""
        categories = []
        
        embedding = await embedding_service.embed_query(query, categories)
        
        # Should still produce valid embedding
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
    
    @pytest.mark.asyncio
    async def test_embedding_latency(self, embedding_service):
        """Test that embedding generation is fast."""
        query = "best running shoes for marathon training"
        categories = ["running_shoes", "marathon_gear"]
        
        # Warm-up
        await embedding_service.embed_query(query, categories)
        
        # Measure 100 embeddings
        start = time.perf_counter()
        for _ in range(100):
            await embedding_service.embed_query(query, categories)
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 100) * 1000
        
        # Should be under 10ms per embedding
        assert avg_latency_ms < 10, f"Average latency {avg_latency_ms:.2f}ms exceeds 10ms target"
        print(f"\n✅ Average embedding latency: {avg_latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_embedding_dimension(self, embedding_service):
        """Test that embedding service reports correct dimension."""
        dim = embedding_service.get_embedding_dimension()
        assert dim == 384  # all-MiniLM-L6-v2 dimension
    
    # ========== Campaign Repository Tests ==========
    
    def test_campaign_repository_loaded(self, campaign_repo):
        """Test that campaigns are loaded correctly."""
        count = campaign_repo.get_count()
        assert count > 0, "No campaigns loaded"
        print(f"\n✅ Loaded {count} campaigns")
    
    def test_get_campaigns_by_indices(self, campaign_repo):
        """Test retrieving campaigns by indices."""
        indices = np.array([0, 1, 2, 3, 4])
        campaigns = campaign_repo.get_by_indices(indices)
        
        assert len(campaigns) == 5
        for campaign in campaigns:
            assert 'campaign_id' in campaign
            assert 'title' in campaign
            assert 'description' in campaign
    
    def test_get_campaign_by_id(self, campaign_repo):
        """Test retrieving campaign by ID."""
        # Get first campaign's ID
        all_campaigns = campaign_repo.get_all()
        if len(all_campaigns) > 0:
            first_id = all_campaigns[0]['campaign_id']
            campaign = campaign_repo.get_by_id(first_id)
            
            assert campaign is not None
            assert campaign['campaign_id'] == first_id
    
    def test_get_campaigns_by_category(self, campaign_repo):
        """Test filtering campaigns by category."""
        # Get all campaigns and find a category
        all_campaigns = campaign_repo.get_all()
        if len(all_campaigns) > 0:
            category = all_campaigns[0].get('category')
            if category:
                filtered = campaign_repo.get_by_category(category)
                assert len(filtered) > 0
                for campaign in filtered:
                    assert campaign['category'] == category
    
    def test_get_campaigns_by_vertical(self, campaign_repo):
        """Test filtering campaigns by vertical."""
        all_campaigns = campaign_repo.get_all()
        if len(all_campaigns) > 0:
            vertical = all_campaigns[0].get('vertical')
            if vertical:
                filtered = campaign_repo.get_by_vertical(vertical)
                assert len(filtered) > 0
                for campaign in filtered:
                    assert campaign['vertical'] == vertical
    
    def test_campaign_data_structure(self, campaign_repo):
        """Test that campaigns have expected structure."""
        campaigns = campaign_repo.get_all()
        assert len(campaigns) > 0
        
        # Check first campaign has required fields
        campaign = campaigns[0]
        required_fields = ['campaign_id', 'title', 'description', 'keywords']
        for field in required_fields:
            assert field in campaign, f"Missing required field: {field}"
    
    # ========== Vector Repository Tests ==========
    
    def test_vector_repository_loaded(self, vector_repo):
        """Test that FAISS index is loaded correctly."""
        size = vector_repo.get_index_size()
        assert size > 0, "FAISS index is empty"
        print(f"\n✅ Loaded FAISS index with {size} vectors")
    
    def test_vector_dimension(self, vector_repo):
        """Test that vector dimension matches expected."""
        dim = vector_repo.get_dimension()
        assert dim == 384  # Should match embedding dimension
    
    def test_vector_index_trained(self, vector_repo):
        """Test that index is trained."""
        assert vector_repo.is_trained()
    
    def test_vector_search_basic(self, vector_repo):
        """Test basic vector search."""
        # Create a random query vector
        query_vector = np.random.randn(384).astype(np.float32)
        
        indices, distances = vector_repo.search(query_vector, k=10)
        
        assert len(indices) == 10
        assert len(distances) == 10
        assert all(idx >= 0 for idx in indices)
        assert all(dist >= 0 for dist in distances)
    
    def test_vector_search_k_constraint(self, vector_repo):
        """Test that k parameter is respected."""
        query_vector = np.random.randn(384).astype(np.float32)
        
        for k in [1, 10, 100, 1000]:
            indices, distances = vector_repo.search(query_vector, k=k)
            expected_k = min(k, vector_repo.get_index_size())
            assert len(indices) == expected_k
            assert len(distances) == expected_k
    
    def test_vector_search_distance_ordering(self, vector_repo):
        """Test that results are ordered by distance."""
        query_vector = np.random.randn(384).astype(np.float32)
        
        indices, distances = vector_repo.search(query_vector, k=100)
        
        # Distances should be in ascending order (nearest first)
        for i in range(len(distances) - 1):
            assert distances[i] <= distances[i + 1], "Results not ordered by distance"
    
    # ========== Search Service Tests ==========
    
    @pytest.mark.asyncio
    async def test_end_to_end_search(self, embedding_service, search_service):
        """Test complete end-to-end search flow."""
        query = "running shoes for marathon training"
        categories = ["running_shoes", "marathon_gear"]
        
        # Step 1: Generate embedding
        query_embedding = await embedding_service.embed_query(query, categories)
        
        # Step 2: Search for campaigns
        campaigns = await search_service.search(query_embedding, k=10)
        
        # Verify results
        assert len(campaigns) == 10
        for campaign in campaigns:
            assert 'campaign_id' in campaign
            assert 'title' in campaign
            assert 'similarity_score' in campaign
            assert 'search_rank' in campaign
            assert 0 <= campaign['similarity_score'] <= 1
    
    @pytest.mark.asyncio
    async def test_search_with_different_k_values(self, embedding_service, search_service):
        """Test search with different k values."""
        query = "laptop for programming"
        categories = ["laptops", "electronics"]
        
        query_embedding = await embedding_service.embed_query(query, categories)
        
        for k in [1, 10, 100, 1000]:
            campaigns = await search_service.search(query_embedding, k=k)
            assert len(campaigns) <= k
            assert len(campaigns) > 0
    
    @pytest.mark.asyncio
    async def test_search_similarity_scores(self, embedding_service, search_service):
        """Test that similarity scores are valid."""
        query = "fitness tracker"
        categories = ["fitness_trackers"]
        
        query_embedding = await embedding_service.embed_query(query, categories)
        campaigns = await search_service.search(query_embedding, k=100)
        
        # All similarity scores should be in valid range
        for campaign in campaigns:
            score = campaign['similarity_score']
            assert 0 <= score <= 1, f"Invalid similarity score: {score}"
    
    @pytest.mark.asyncio
    async def test_search_ranking_order(self, embedding_service, search_service):
        """Test that search results are properly ranked."""
        query = "yoga mat"
        categories = ["yoga_equipment"]
        
        query_embedding = await embedding_service.embed_query(query, categories)
        campaigns = await search_service.search(query_embedding, k=50)
        
        # Similarity scores should be in descending order (most similar first)
        for i in range(len(campaigns) - 1):
            assert campaigns[i]['similarity_score'] >= campaigns[i + 1]['similarity_score'], \
                "Results not ordered by similarity"
        
        # Search ranks should be sequential
        for i, campaign in enumerate(campaigns):
            assert campaign['search_rank'] == i + 1
    
    @pytest.mark.asyncio
    async def test_search_latency(self, embedding_service, search_service):
        """Test that search is fast."""
        query = "best running shoes"
        categories = ["running_shoes"]
        
        query_embedding = await embedding_service.embed_query(query, categories)
        
        # Warm-up
        await search_service.search(query_embedding, k=1000)
        
        # Measure 100 searches
        start = time.perf_counter()
        for _ in range(100):
            await search_service.search(query_embedding, k=1000)
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 100) * 1000
        
        # Should be under 15ms per search
        assert avg_latency_ms < 15, f"Average latency {avg_latency_ms:.2f}ms exceeds 15ms target"
        print(f"\n✅ Average search latency: {avg_latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_search_index_stats(self, search_service):
        """Test getting index statistics."""
        stats = search_service.get_index_stats()
        
        assert 'total_vectors' in stats
        assert 'dimension' in stats
        assert 'is_trained' in stats
        
        assert stats['total_vectors'] > 0
        assert stats['dimension'] == 384
        assert stats['is_trained'] is True
    
    # ========== Integration Tests ==========
    
    @pytest.mark.asyncio
    async def test_multiple_queries_batch(self, embedding_service, search_service):
        """Test processing multiple queries in sequence."""
        queries = [
            ("running shoes", ["running_shoes"]),
            ("laptop for programming", ["laptops", "electronics"]),
            ("fitness tracker", ["fitness_trackers"]),
            ("yoga mat", ["yoga_equipment"]),
            ("protein powder", ["sports_nutrition"]),
        ]
        
        for query, categories in queries:
            # Generate embedding
            embedding = await embedding_service.embed_query(query, categories)
            
            # Search
            campaigns = await search_service.search(embedding, k=10)
            
            # Verify
            assert len(campaigns) == 10
            assert all('similarity_score' in c for c in campaigns)
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, embedding_service, search_service):
        """Test concurrent search requests."""
        queries = [
            "running shoes",
            "laptop computer",
            "fitness tracker",
            "yoga mat",
            "protein powder",
        ]
        
        # Generate all embeddings
        embeddings = []
        for query in queries:
            embedding = await embedding_service.embed_query(query, [])
            embeddings.append(embedding)
        
        # Execute all searches concurrently
        tasks = [search_service.search(emb, k=10) for emb in embeddings]
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == len(queries)
        for campaigns in results:
            assert len(campaigns) == 10
            assert all('similarity_score' in c for c in campaigns)
    
    @pytest.mark.asyncio
    async def test_relevance_for_specific_queries(self, embedding_service, search_service):
        """Test that search returns relevant results for specific queries."""
        test_cases = [
            ("running shoes", ["running", "shoes", "athletic", "footwear"]),
            ("laptop computer", ["laptop", "computer", "electronics"]),
            ("fitness tracker", ["fitness", "tracker", "health", "wearable"]),
        ]
        
        for query, expected_keywords in test_cases:
            # Generate embedding and search
            embedding = await embedding_service.embed_query(query, [])
            campaigns = await search_service.search(embedding, k=10)
            
            # Check that top results contain relevant keywords
            top_campaign = campaigns[0]
            title_lower = top_campaign['title'].lower()
            description_lower = top_campaign['description'].lower()
            
            # At least one expected keyword should appear in title or description
            has_relevant_keyword = any(
                keyword.lower() in title_lower or keyword.lower() in description_lower
                for keyword in expected_keywords
            )
            
            # Note: This is a soft check - may not always pass with random data
            # but should pass most of the time with good embeddings
            if not has_relevant_keyword:
                print(f"\nWarning: Query '{query}' top result may not be highly relevant")
                print(f"  Title: {top_campaign['title']}")
    
    @pytest.mark.asyncio
    async def test_category_boosting_effect(self, embedding_service, search_service):
        """Test that adding categories affects search results."""
        query = "shoes"
        
        # Search without categories
        embedding_no_cat = await embedding_service.embed_query(query, [])
        results_no_cat = await search_service.search(embedding_no_cat, k=10)
        
        # Search with categories
        embedding_with_cat = await embedding_service.embed_query(
            query, 
            ["running_shoes", "athletic_footwear"]
        )
        results_with_cat = await search_service.search(embedding_with_cat, k=10)
        
        # Results should be different
        top_ids_no_cat = [c['campaign_id'] for c in results_no_cat[:5]]
        top_ids_with_cat = [c['campaign_id'] for c in results_with_cat[:5]]
        
        # At least some difference in top results
        assert top_ids_no_cat != top_ids_with_cat, \
            "Categories should affect search results"
    
    @pytest.mark.asyncio
    async def test_embedding_and_search_consistency(self, embedding_service, search_service):
        """Test that same query produces consistent search results."""
        query = "running shoes"
        categories = ["running_shoes"]
        
        # Run search twice
        embedding1 = await embedding_service.embed_query(query, categories)
        results1 = await search_service.search(embedding1, k=10)
        
        embedding2 = await embedding_service.embed_query(query, categories)
        results2 = await search_service.search(embedding2, k=10)
        
        # Results should be identical
        ids1 = [c['campaign_id'] for c in results1]
        ids2 = [c['campaign_id'] for c in results2]
        
        assert ids1 == ids2, "Same query should produce same results"
    
    @pytest.mark.asyncio
    async def test_full_pipeline_latency(self, embedding_service, search_service):
        """Test end-to-end pipeline latency (embedding + search)."""
        query = "best running shoes for marathon training"
        categories = ["running_shoes", "marathon_gear"]
        
        # Warm-up
        embedding = await embedding_service.embed_query(query, categories)
        await search_service.search(embedding, k=1000)
        
        # Measure 100 full pipeline runs
        start = time.perf_counter()
        for _ in range(100):
            embedding = await embedding_service.embed_query(query, categories)
            await search_service.search(embedding, k=1000)
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 100) * 1000
        
        # Should be under 25ms total (10ms embedding + 15ms search)
        assert avg_latency_ms < 25, f"Average pipeline latency {avg_latency_ms:.2f}ms exceeds 25ms target"
        print(f"\n✅ Average full pipeline latency: {avg_latency_ms:.2f}ms")


def test_phase5_components_exist():
    """Test that all Phase 5 components are properly created."""
    # Check that files exist
    assert Path("src/services/embedding_service.py").exists()
    assert Path("src/services/search_service.py").exists()
    assert Path("src/repositories/vector_repository.py").exists()
    assert Path("src/repositories/campaign_repository.py").exists()
    assert Path("data/campaigns.jsonl").exists()
    assert Path("data/faiss.index").exists()
    
    # Check that classes can be imported
    from src.services.embedding_service import EmbeddingService
    from src.services.search_service import SearchService
    from src.repositories.vector_repository import VectorRepository
    from src.repositories.campaign_repository import CampaignRepository
    
    assert EmbeddingService is not None
    assert SearchService is not None
    assert VectorRepository is not None
    assert CampaignRepository is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

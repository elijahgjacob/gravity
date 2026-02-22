"""
Unit tests for Phase 5 components (without full index).

Tests individual components of the embedding and search system.
"""

import pytest
import asyncio
import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.embedding_service import EmbeddingService
from src.repositories.campaign_repository import CampaignRepository


class TestEmbeddingService:
    """Test EmbeddingService functionality."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service fixture."""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_embedding_service_initialization(self, embedding_service):
        """Test that embedding service initializes correctly."""
        assert embedding_service.model is not None
        assert embedding_service.embedding_dim == 384  # all-MiniLM-L6-v2
        assert embedding_service.model_name == 'all-MiniLM-L6-v2'
    
    @pytest.mark.asyncio
    async def test_embed_query_basic(self, embedding_service):
        """Test basic query embedding."""
        query = "running shoes for marathon"
        categories = ["running_shoes", "marathon_gear"]
        
        embedding = await embedding_service.embed_query(query, categories)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
    
    @pytest.mark.asyncio
    async def test_embed_query_no_categories(self, embedding_service):
        """Test query embedding without categories."""
        query = "running shoes"
        categories = []
        
        embedding = await embedding_service.embed_query(query, categories)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
    
    @pytest.mark.asyncio
    async def test_embed_query_similarity(self, embedding_service):
        """Test that similar queries have similar embeddings."""
        query1 = "running shoes for marathon"
        query2 = "marathon running shoes"
        query3 = "laptop for programming"
        
        emb1 = await embedding_service.embed_query(query1, [])
        emb2 = await embedding_service.embed_query(query2, [])
        emb3 = await embedding_service.embed_query(query3, [])
        
        # Cosine similarity
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_12 = cosine_sim(emb1, emb2)
        sim_13 = cosine_sim(emb1, emb3)
        
        # Similar queries should have higher similarity
        assert sim_12 > sim_13
        assert sim_12 > 0.8  # Very similar queries
    
    def test_embed_campaigns_batch(self, embedding_service):
        """Test batch campaign embedding."""
        campaigns = [
            {
                "title": "Nike Running Shoes",
                "description": "Best shoes for marathon training",
                "keywords": ["running", "shoes", "marathon"]
            },
            {
                "title": "MacBook Pro",
                "description": "Laptop for developers",
                "keywords": ["laptop", "programming", "developer"]
            }
        ]
        
        embeddings = embedding_service.embed_campaigns_batch(
            campaigns,
            batch_size=2,
            show_progress=False
        )
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 384)
        assert embeddings.dtype == np.float32
    
    def test_get_embedding_dimension(self, embedding_service):
        """Test getting embedding dimension."""
        dim = embedding_service.get_embedding_dimension()
        assert dim == 384


class TestCampaignRepository:
    """Test CampaignRepository functionality."""
    
    @pytest.fixture
    def campaign_repo(self):
        """Create campaign repository fixture."""
        return CampaignRepository("data/campaigns.jsonl")
    
    def test_repository_initialization(self, campaign_repo):
        """Test that repository loads campaigns."""
        assert campaign_repo.get_count() > 0
        print(f"Loaded {campaign_repo.get_count()} campaigns")
    
    def test_get_by_indices(self, campaign_repo):
        """Test getting campaigns by indices."""
        indices = np.array([0, 1, 2])
        campaigns = campaign_repo.get_by_indices(indices)
        
        assert len(campaigns) == 3
        assert all('campaign_id' in c for c in campaigns)
        assert all('title' in c for c in campaigns)
    
    def test_get_by_indices_out_of_bounds(self, campaign_repo):
        """Test handling of out-of-bounds indices."""
        total = campaign_repo.get_count()
        indices = np.array([0, total + 100])  # One valid, one invalid
        campaigns = campaign_repo.get_by_indices(indices)
        
        # Should only return valid campaigns
        assert len(campaigns) == 1
    
    def test_get_by_id(self, campaign_repo):
        """Test getting campaign by ID."""
        # Get first campaign's ID
        all_campaigns = campaign_repo.get_all()
        first_id = all_campaigns[0]['campaign_id']
        
        campaign = campaign_repo.get_by_id(first_id)
        assert campaign is not None
        assert campaign['campaign_id'] == first_id
    
    def test_get_by_id_not_found(self, campaign_repo):
        """Test getting non-existent campaign."""
        campaign = campaign_repo.get_by_id("nonexistent_id_xyz")
        assert campaign is None
    
    def test_get_by_category(self, campaign_repo):
        """Test filtering by category."""
        # Get a category from first campaign
        all_campaigns = campaign_repo.get_all()
        category = all_campaigns[0]['category']
        
        campaigns = campaign_repo.get_by_category(category)
        assert len(campaigns) > 0
        assert all(c['category'] == category for c in campaigns)
    
    def test_get_by_vertical(self, campaign_repo):
        """Test filtering by vertical."""
        # Get a vertical from first campaign
        all_campaigns = campaign_repo.get_all()
        vertical = all_campaigns[0]['vertical']
        
        campaigns = campaign_repo.get_by_vertical(vertical)
        assert len(campaigns) > 0
        assert all(c['vertical'] == vertical for c in campaigns)
    
    def test_get_all(self, campaign_repo):
        """Test getting all campaigns."""
        campaigns = campaign_repo.get_all()
        assert len(campaigns) == campaign_repo.get_count()
        assert all(isinstance(c, dict) for c in campaigns)


def test_phase5_components_exist():
    """Test that all Phase 5 components are properly created."""
    # Check that files exist
    assert Path("src/services/embedding_service.py").exists()
    assert Path("src/services/search_service.py").exists()
    assert Path("src/repositories/vector_repository.py").exists()
    assert Path("src/repositories/campaign_repository.py").exists()
    assert Path("scripts/build_index.py").exists()
    
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

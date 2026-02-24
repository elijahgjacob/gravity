"""
SERVICE: Business logic for campaign search.

This service performs vector similarity search and retrieves
campaign data using FAISS and the campaign repository.
"""

import numpy as np

from src.repositories.campaign_repository import CampaignRepository
from src.repositories.vector_repository import VectorRepository


class SearchService:
    """
    SERVICE: Business logic for campaign search.

    Performs vector similarity search using FAISS and enriches
    results with campaign metadata and similarity scores.

    Performance: ~10-15ms for 10k vectors
    """

    def __init__(self, vector_repo: VectorRepository, campaign_repo: CampaignRepository):
        """
        Initialize the search service.

        Args:
            vector_repo: Repository for FAISS vector index
            campaign_repo: Repository for campaign metadata
        """
        self.vector_repo = vector_repo
        self.campaign_repo = campaign_repo

    async def search(self, query_embedding: np.ndarray, k: int = 1000) -> list[dict]:
        """
        Search for top-k most similar campaigns.

        Performs the following steps:
        1. Vector similarity search using FAISS (~10ms)
        2. Retrieve campaign metadata for matched indices
        3. Attach similarity scores to each campaign

        Args:
            query_embedding: Query vector from EmbeddingService
            k: Number of campaigns to retrieve (default: 1000)

        Returns:
            List of campaign dictionaries with added 'similarity_score' field
        """
        # Step 1: Vector search using FAISS
        # Returns indices and L2 distances
        indices, distances = self.vector_repo.search(query_embedding, k)

        # Step 2: Retrieve campaign data for matched indices
        campaigns = self.campaign_repo.get_by_indices(indices)

        # Step 3: Attach similarity scores
        # Convert L2 distance to similarity score (0-1 range)
        # Lower distance = higher similarity
        # Formula: similarity = 1 / (1 + distance)
        for i, campaign in enumerate(campaigns):
            distance = float(distances[i])
            similarity_score = 1.0 / (1.0 + distance)
            campaign["similarity_score"] = similarity_score
            campaign["search_rank"] = i + 1  # 1-indexed rank

        return campaigns

    def get_index_stats(self) -> dict:
        """
        Get statistics about the vector index.

        Returns:
            Dictionary with index statistics:
            - total_vectors: Number of vectors in index
            - dimension: Vector dimensionality
            - is_trained: Whether index is trained
        """
        return {
            "total_vectors": self.vector_repo.get_index_size(),
            "dimension": self.vector_repo.get_dimension(),
            "is_trained": self.vector_repo.is_trained(),
        }

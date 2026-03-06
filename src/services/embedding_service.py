"""
SERVICE: Business logic for text embedding.

This service converts queries and campaigns to vector representations
using sentence-transformers for semantic similarity search.
"""

import os
import numpy as np
from functools import lru_cache
from cachetools import TTLCache

# Set threading environment variables BEFORE importing torch
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    SERVICE: Business logic for text embedding.

    Converts queries and campaigns to 384-dimensional vector representations
    using sentence-transformers for fast, local inference.

    Performance: ~5-15ms per query embedding on CPU (cached: <1ms)
    """

    def __init__(self, model_name: str = "paraphrase-MiniLM-L3-v2"):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
                       Default: paraphrase-MiniLM-L3-v2 (384 dims, ~2x faster than L6)
        """
        self.model_name = model_name
        
        # Set number of threads for CPU inference
        torch.set_num_threads(4)
        torch.set_num_interop_threads(2)
        
        # Load model
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Set model to eval mode for inference
        self.model.eval()
        
        # Cache for embeddings (1000 entries, 1 hour TTL)
        self._embedding_cache = TTLCache(maxsize=1000, ttl=3600)
        
        print(f"Loaded embedding model: {model_name} ({self.embedding_dim} dimensions)")

    async def embed_query(self, query: str, categories: list) -> np.ndarray:
        """
        Embed query text combined with extracted categories.

        Combines the query with category names to create a richer embedding
        that captures both the user's intent and the extracted categories.

        Args:
            query: The user's query text
            categories: List of extracted category names

        Returns:
            numpy array of shape (embedding_dim,) - typically 384 dimensions
        """
        # Combine query + top 3 categories for richer embedding
        category_text = " ".join(sorted(categories[:3])) if categories else ""
        combined_text = f"{query} {category_text}".strip()
        
        # Check cache first
        cache_key = combined_text.lower()
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # Generate embedding with optimized settings
        with torch.no_grad():
            embedding = self.model.encode(
                combined_text, 
                convert_to_numpy=True, 
                show_progress_bar=False,
                normalize_embeddings=True
            )
        
        # Cache the result
        self._embedding_cache[cache_key] = embedding

        return embedding

    def embed_campaigns_batch(
        self, campaigns: list, batch_size: int = 32, show_progress: bool = True
    ) -> np.ndarray:
        """
        Batch embed campaigns for offline index building.

        Combines campaign title, description, and keywords into a single
        text representation, then generates embeddings for all campaigns.

        This is used offline to pre-compute embeddings for the FAISS index.

        Args:
            campaigns: List of campaign dictionaries with title, description, keywords
            batch_size: Number of campaigns to embed at once (default: 32)
            show_progress: Whether to show progress bar (default: True)

        Returns:
            numpy array of shape (N, embedding_dim) where N is number of campaigns
        """
        # Create text representations for each campaign
        texts = []
        for campaign in campaigns:
            # Combine title, description, and keywords
            title = campaign.get("title", "")
            description = campaign.get("description", "")
            keywords = " ".join(campaign.get("keywords", []))

            # Create rich text representation
            text = f"{title} {description} {keywords}".strip()
            texts.append(text)

        # Batch encode all campaigns (normalized to match query embeddings)
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
            normalize_embeddings=True,  # Must match query embedding normalization
        )

        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of embeddings produced by this service.

        Returns:
            Integer dimension (typically 384 for all-MiniLM-L6-v2)
        """
        return self.embedding_dim

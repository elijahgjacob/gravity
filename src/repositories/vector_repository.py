"""
REPOSITORY: Data access for FAISS vector index.

This repository handles loading and querying the FAISS vector index
for fast similarity search over campaign embeddings.
"""

import faiss
import numpy as np
from typing import Tuple, Optional
from pathlib import Path


class VectorRepository:
    """
    REPOSITORY: Data access for FAISS vector index.
    
    Loads a pre-built FAISS index from disk and provides fast
    k-nearest neighbor search for campaign retrieval.
    """
    
    def __init__(self, index_path: str):
        """
        Initialize the vector repository.
        
        Args:
            index_path: Path to the FAISS index file
        """
        self.index: Optional[faiss.Index] = None
        self.index_path = index_path
        self._load_index(index_path)
    
    def _load_index(self, path: str) -> None:
        """
        Load FAISS index from disk.
        
        Args:
            path: Path to the FAISS index file
        
        Raises:
            FileNotFoundError: If index file doesn't exist
            RuntimeError: If index loading fails
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"FAISS index not found at {path}")
        
        try:
            self.index = faiss.read_index(path)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors from {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS index: {e}")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for k nearest neighbors.
        
        Performs L2 distance-based similarity search in the FAISS index.
        
        Args:
            query_embedding: Query vector (1D or 2D array)
            k: Number of nearest neighbors to return (default: 1000)
        
        Returns:
            Tuple of (indices, distances):
            - indices: Array of campaign indices (shape: (k,))
            - distances: Array of L2 distances (shape: (k,))
        
        Raises:
            ValueError: If index is not loaded or k is invalid
        """
        if self.index is None:
            raise ValueError("FAISS index not loaded")
        
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        
        # Ensure k doesn't exceed total vectors in index
        k = min(k, self.index.ntotal)
        
        # Ensure query is 2D (FAISS expects shape: (n_queries, dimension))
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure float32 dtype (FAISS requirement)
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        # Perform search
        # Returns: distances (n_queries, k), indices (n_queries, k)
        distances, indices = self.index.search(query_embedding, k)
        
        # Return flattened arrays (we only have 1 query)
        return indices[0], distances[0]
    
    def get_index_size(self) -> int:
        """
        Get the number of vectors in the index.
        
        Returns:
            Number of vectors in the index
        """
        if self.index is None:
            return 0
        return self.index.ntotal
    
    def get_dimension(self) -> int:
        """
        Get the dimensionality of vectors in the index.
        
        Returns:
            Vector dimension
        """
        if self.index is None:
            return 0
        return self.index.d
    
    def is_trained(self) -> bool:
        """
        Check if the index is trained.
        
        For IndexFlatL2, this always returns True as no training is needed.
        For other index types (IVF, etc.), this indicates training status.
        
        Returns:
            True if index is trained, False otherwise
        """
        if self.index is None:
            return False
        return self.index.is_trained

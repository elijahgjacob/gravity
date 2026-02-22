"""
Build FAISS index from campaign embeddings.

This script:
1. Loads campaigns from data/campaigns.jsonl
2. Generates embeddings using sentence-transformers
3. Builds a FAISS index (IndexFlatL2)
4. Saves embeddings and index to disk

Usage:
    python scripts/build_index.py
"""

import sys
from pathlib import Path
import numpy as np
import faiss
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.embedding_service import EmbeddingService
from src.repositories.campaign_repository import CampaignRepository


def build_faiss_index(
    campaigns_path: str = "data/campaigns.jsonl",
    embeddings_path: str = "data/embeddings.npy",
    index_path: str = "data/faiss.index",
    batch_size: int = 32
):
    """
    Build FAISS index from campaigns.
    
    Args:
        campaigns_path: Path to campaigns JSONL file
        embeddings_path: Path to save embeddings (.npy)
        index_path: Path to save FAISS index
        batch_size: Batch size for embedding generation
    """
    print("=" * 80)
    print("BUILDING FAISS INDEX")
    print("=" * 80)
    
    # Step 1: Load campaigns
    print(f"\n[1/4] Loading campaigns from {campaigns_path}...")
    start = time.perf_counter()
    campaign_repo = CampaignRepository(campaigns_path)
    campaigns = campaign_repo.get_all()
    load_time = time.perf_counter() - start
    print(f"✓ Loaded {len(campaigns)} campaigns in {load_time:.2f}s")
    
    if len(campaigns) == 0:
        print("❌ No campaigns found. Exiting.")
        return
    
    # Step 2: Initialize embedding service
    print(f"\n[2/4] Initializing embedding service...")
    start = time.perf_counter()
    embedding_service = EmbeddingService()
    init_time = time.perf_counter() - start
    print(f"✓ Initialized in {init_time:.2f}s")
    print(f"  Model: {embedding_service.model_name}")
    print(f"  Dimension: {embedding_service.get_embedding_dimension()}")
    
    # Step 3: Generate embeddings
    print(f"\n[3/4] Generating embeddings (batch_size={batch_size})...")
    start = time.perf_counter()
    embeddings = embedding_service.embed_campaigns_batch(
        campaigns,
        batch_size=batch_size,
        show_progress=True
    )
    embed_time = time.perf_counter() - start
    print(f"✓ Generated {len(embeddings)} embeddings in {embed_time:.2f}s")
    print(f"  Shape: {embeddings.shape}")
    print(f"  Dtype: {embeddings.dtype}")
    print(f"  Avg time per campaign: {embed_time / len(campaigns) * 1000:.2f}ms")
    
    # Save embeddings to disk
    print(f"\n  Saving embeddings to {embeddings_path}...")
    np.save(embeddings_path, embeddings)
    embeddings_size_mb = Path(embeddings_path).stat().st_size / (1024 * 1024)
    print(f"✓ Saved embeddings ({embeddings_size_mb:.2f} MB)")
    
    # Step 4: Build FAISS index
    print(f"\n[4/4] Building FAISS index...")
    start = time.perf_counter()
    
    # Get dimension from embeddings
    dimension = embeddings.shape[1]
    
    # Create IndexFlatL2 (exact L2 distance search, no training needed)
    # This is optimal for <100k vectors
    index = faiss.IndexFlatL2(dimension)
    
    # Ensure embeddings are float32 (FAISS requirement)
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype(np.float32)
    
    # Add vectors to index
    index.add(embeddings)
    
    build_time = time.perf_counter() - start
    print(f"✓ Built FAISS index in {build_time:.2f}s")
    print(f"  Index type: IndexFlatL2")
    print(f"  Total vectors: {index.ntotal}")
    print(f"  Dimension: {index.d}")
    print(f"  Is trained: {index.is_trained}")
    
    # Save index to disk
    print(f"\n  Saving index to {index_path}...")
    faiss.write_index(index, index_path)
    index_size_mb = Path(index_path).stat().st_size / (1024 * 1024)
    print(f"✓ Saved FAISS index ({index_size_mb:.2f} MB)")
    
    # Summary
    print("\n" + "=" * 80)
    print("BUILD COMPLETE")
    print("=" * 80)
    total_time = load_time + init_time + embed_time + build_time
    print(f"\nTotal time: {total_time:.2f}s")
    print(f"  - Loading campaigns: {load_time:.2f}s")
    print(f"  - Initializing model: {init_time:.2f}s")
    print(f"  - Generating embeddings: {embed_time:.2f}s")
    print(f"  - Building index: {build_time:.2f}s")
    
    print(f"\nOutput files:")
    print(f"  - Embeddings: {embeddings_path} ({embeddings_size_mb:.2f} MB)")
    print(f"  - FAISS index: {index_path} ({index_size_mb:.2f} MB)")
    
    print(f"\n✓ Index ready for use!")
    print(f"  {len(campaigns)} campaigns indexed")
    print(f"  {dimension} dimensions per vector")
    
    # Quick validation test
    print("\n" + "=" * 80)
    print("VALIDATION TEST")
    print("=" * 80)
    
    print("\nTesting index with sample query...")
    test_query = "running shoes for marathon"
    test_embedding = embedding_service.model.encode(test_query, convert_to_numpy=True)
    test_embedding = test_embedding.reshape(1, -1).astype(np.float32)
    
    k = min(10, index.ntotal)
    distances, indices = index.search(test_embedding, k)
    
    print(f"✓ Search successful!")
    print(f"  Query: '{test_query}'")
    print(f"  Top {k} results:")
    
    for i, (idx, dist) in enumerate(zip(indices[0][:5], distances[0][:5]), 1):
        campaign = campaigns[idx]
        similarity = 1.0 / (1.0 + dist)
        print(f"    {i}. {campaign['title'][:60]}... (similarity: {similarity:.4f})")


if __name__ == "__main__":
    build_faiss_index()

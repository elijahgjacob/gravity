"""
CONTROLLER: Orchestrates service calls for ad retrieval.

This controller handles the complete ad retrieval pipeline:
1. Parallel eligibility scoring and category extraction
2. Short-circuit if eligibility is 0.0
3. Query embedding generation
4. Vector similarity search
5. Relevance ranking
6. Return top 1000 campaigns
"""

import asyncio
import time
from typing import Optional

from src.api.models.requests import RetrievalRequest
from src.api.models.responses import RetrievalResponse, Campaign
from src.services.eligibility_service import EligibilityService
from src.services.category_service import CategoryService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.ranking_service import RankingService
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class RetrievalController:
    """
    CONTROLLER: Orchestrates service calls for ad retrieval.
    
    Coordinates the complete retrieval pipeline with parallel execution
    and optimized flow control for sub-100ms latency.
    
    Target Latency: < 100ms (p95)
    """
    
    def __init__(
        self,
        eligibility_service: EligibilityService,
        category_service: CategoryService,
        embedding_service: EmbeddingService,
        search_service: SearchService,
        ranking_service: RankingService
    ):
        """
        Initialize the retrieval controller.
        
        Args:
            eligibility_service: Service for ad eligibility scoring
            category_service: Service for category extraction
            embedding_service: Service for query embedding
            search_service: Service for vector similarity search
            ranking_service: Service for relevance ranking
        """
        self.eligibility_service = eligibility_service
        self.category_service = category_service
        self.embedding_service = embedding_service
        self.search_service = search_service
        self.ranking_service = ranking_service
    
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Execute the complete ad retrieval pipeline.
        
        Pipeline Flow:
        1. Parallel: eligibility scoring + category extraction (30-40ms)
        2. Short-circuit if eligibility = 0.0 (return empty campaigns)
        3. Query embedding generation (5-10ms)
        4. Vector similarity search (10-15ms)
        5. Relevance ranking (10-20ms)
        6. Return top 1000 campaigns
        
        Args:
            request: Retrieval request with query and optional context
        
        Returns:
            Retrieval response with campaigns and metadata
        """
        start_time = time.perf_counter()
        
        # Convert context to dict if present
        context_dict = request.context.model_dump() if request.context else None
        
        logger.info(f"Starting retrieval for query: '{request.query[:50]}...'")
        
        # Phase 1: Parallel processing of eligibility and categories
        logger.debug("Phase 1: Parallel eligibility + category extraction")
        eligibility_task = self.eligibility_service.score(
            request.query, 
            context_dict
        )
        categories_task = self.category_service.extract(
            request.query,
            context_dict
        )
        
        eligibility_result, categories = await asyncio.gather(
            eligibility_task, 
            categories_task
        )
        
        # Unpack eligibility result (score, rejection_reason)
        eligibility, rejection_reason = eligibility_result
        
        logger.debug(f"Eligibility: {eligibility}, Categories: {categories}")
        
        # Short-circuit if ad_eligibility is 0.0
        if eligibility == 0.0:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Short-circuited (eligibility=0.0) in {latency_ms:.2f}ms - Reason: {rejection_reason}")
            
            return RetrievalResponse(
                ad_eligibility=0.0,
                extracted_categories=categories,
                campaigns=[],
                latency_ms=latency_ms,
                metadata={
                    "short_circuited": True,
                    "reason": rejection_reason or "Zero eligibility score"
                }
            )
        
        # Phase 2: Embedding generation
        logger.debug("Phase 2: Query embedding")
        query_embedding = await self.embedding_service.embed_query(
            request.query, 
            categories
        )
        
        # Phase 3: Vector similarity search
        logger.debug("Phase 3: Vector search")
        candidates = await self.search_service.search(
            query_embedding, 
            k=1500  # Retrieve more than 1000 for better ranking
        )
        
        logger.debug(f"Retrieved {len(candidates)} candidates")
        
        # Phase 4: Relevance ranking
        logger.debug("Phase 4: Relevance ranking")
        ranked_campaigns = await self.ranking_service.rank(
            candidates,
            request.query,
            categories,
            context_dict
        )
        
        # Return top 1000 (or fewer if less available)
        final_campaigns = ranked_campaigns[:1000]
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"Retrieval complete: {len(final_campaigns)} campaigns in {latency_ms:.2f}ms"
        )
        
        # Convert to response models
        campaign_models = [
            Campaign(
                campaign_id=c['campaign_id'],
                relevance_score=c['relevance_score'],
                title=c['title'],
                category=c['category'],
                description=c.get('description', ''),
                keywords=c.get('keywords', [])
            )
            for c in final_campaigns
        ]
        
        return RetrievalResponse(
            ad_eligibility=eligibility,
            extracted_categories=categories,
            campaigns=campaign_models,
            latency_ms=latency_ms,
            metadata={
                "candidates_retrieved": len(candidates),
                "campaigns_returned": len(campaign_models),
                "top_relevance_score": campaign_models[0].relevance_score if campaign_models else 0.0
            }
        )

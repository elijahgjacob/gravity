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

from src.api.models.requests import RetrievalRequest
from src.api.models.responses import Campaign, RetrievalResponse
from src.core.logging_config import get_logger
from src.services.category_service import CategoryService
from src.services.eligibility_service import EligibilityService
from src.services.embedding_service import EmbeddingService
from src.services.ranking_service import RankingService
from src.services.search_service import SearchService
from typing import Optional

# Import GraphitiService with try-except for graceful degradation
try:
    from src.services.graphiti_service import GraphitiService
except ImportError:
    GraphitiService = None

# Import profile services
try:
    from src.repositories.profile_repository import ProfileRepository
    from src.services.profile_analyzer import ProfileAnalyzer
except ImportError:
    ProfileRepository = None
    ProfileAnalyzer = None

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
        ranking_service: RankingService,
        graphiti_service: Optional['GraphitiService'] = None,
        profile_repo: Optional['ProfileRepository'] = None,
        profile_analyzer: Optional['ProfileAnalyzer'] = None
    ):
        """
        Initialize the retrieval controller.

        Args:
            eligibility_service: Service for ad eligibility scoring
            category_service: Service for category extraction
            embedding_service: Service for query embedding
            search_service: Service for vector similarity search
            ranking_service: Service for relevance ranking
            graphiti_service: Optional service for knowledge graph recording
            profile_repo: Optional repository for user profile storage
            profile_analyzer: Optional service for profile analysis
        """
        self.eligibility_service = eligibility_service
        self.category_service = category_service
        self.embedding_service = embedding_service
        self.search_service = search_service
        self.ranking_service = ranking_service
        self.graphiti_service = graphiti_service
        self.profile_repo = profile_repo
        self.profile_analyzer = profile_analyzer
        
        if graphiti_service:
            logger.info("Graphiti service enabled for controller")
        else:
            logger.debug("Graphiti service not available")
        
        if profile_repo and profile_analyzer:
            logger.info("Profile analysis enabled for controller")
        else:
            logger.debug("Profile analysis not available")

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Execute the complete ad retrieval pipeline.

        Pipeline Flow:
        0. Profile lookup for inferred categories (1-2ms, optional)
        1. Parallel: eligibility scoring + category extraction (30-40ms)
        2. Short-circuit if eligibility = 0.0 (return empty campaigns)
        3. Query embedding generation (5-10ms)
        4. Vector similarity search (10-15ms)
        5. Relevance ranking (10-20ms)
        6. Return top 1000 campaigns
        7. Async: Update profile and trigger analysis (0ms impact)

        Args:
            request: Retrieval request with query and optional context

        Returns:
            Retrieval response with campaigns and metadata
        """
        start_time = time.perf_counter()

        # Convert context to dict if present
        context_dict = request.context.model_dump() if request.context else None

        logger.info(f"Starting retrieval for query: '{request.query[:50]}...'")

        # Phase 0: Profile lookup for inferred categories (fast, in-memory)
        inferred_categories = []
        if request.user_id and self.profile_repo:
            try:
                inferred_categories = await self.profile_repo.get_inferred_categories(request.user_id)
                if inferred_categories:
                    logger.debug(f"Found {len(inferred_categories)} inferred categories for user {request.user_id}")
            except Exception as e:
                logger.warning(f"Profile lookup failed (non-critical): {e}")

        # Phase 1: Parallel processing of eligibility and categories
        logger.debug("Phase 1: Parallel eligibility + category extraction")
        eligibility_task = self.eligibility_service.score(request.query, context_dict)
        categories_task = self.category_service.extract(request.query, context_dict)

        eligibility_result, extracted_categories = await asyncio.gather(eligibility_task, categories_task)
        
        # Merge extracted categories with inferred categories
        categories = list(set(extracted_categories + inferred_categories))
        logger.debug(f"Categories: {len(extracted_categories)} extracted + {len(inferred_categories)} inferred = {len(categories)} total")

        # Unpack eligibility result (score, rejection_reason)
        eligibility, rejection_reason = eligibility_result

        logger.debug(f"Eligibility: {eligibility}, Categories: {categories}")

        # Short-circuit if ad_eligibility is 0.0
        if eligibility == 0.0:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Short-circuited (eligibility=0.0) in {latency_ms:.2f}ms - Reason: {rejection_reason}"
            )

            return RetrievalResponse(
                ad_eligibility=0.0,
                extracted_categories=categories,
                campaigns=[],
                latency_ms=latency_ms,
                metadata={
                    "short_circuited": True,
                    "reason": rejection_reason or "Zero eligibility score",
                },
            )

        # Phase 2: Embedding generation
        logger.debug("Phase 2: Query embedding")
        query_embedding = await self.embedding_service.embed_query(request.query, categories)

        # Phase 3: Vector similarity search
        logger.debug("Phase 3: Vector search")
        candidates = await self.search_service.search(
            query_embedding, k=1500  # Retrieve more than 1000 for better ranking
        )

        logger.debug(f"Retrieved {len(candidates)} candidates")

        # Phase 4: Relevance ranking
        logger.debug("Phase 4: Relevance ranking")
        ranked_campaigns = await self.ranking_service.rank(
            candidates, request.query, categories, context_dict
        )

        # Return top 1000 (or fewer if less available)
        final_campaigns = ranked_campaigns[:1000]

        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Retrieval complete: {len(final_campaigns)} campaigns in {latency_ms:.2f}ms")

        # Convert to response models
        campaign_models = [
            Campaign(
                campaign_id=c["campaign_id"],
                relevance_score=c["relevance_score"],
                title=c["title"],
                category=c["category"],
                description=c.get("description", ""),
                keywords=c.get("keywords", []),
            )
            for c in final_campaigns
        ]
        
        # Build response
        response = RetrievalResponse(
            ad_eligibility=eligibility,
            extracted_categories=categories,
            campaigns=campaign_models,
            latency_ms=latency_ms,
            metadata={
                "candidates_retrieved": len(candidates),
                "campaigns_returned": len(campaign_models),
                "top_relevance_score": (
                    campaign_models[0].relevance_score if campaign_models else 0.0
                ),
            },
        )
        
        # Fire-and-forget: Record to Graphiti (no latency impact)
        if self.graphiti_service:
            asyncio.create_task(
                self._record_to_graphiti_safe(
                    request, eligibility, categories, campaign_models, context_dict
                )
            )
        
        # Fire-and-forget: Update profile and trigger analysis (no latency impact)
        if request.user_id and self.profile_repo:
            asyncio.create_task(
                self._update_profile_safe(
                    request, extracted_categories, context_dict
                )
            )
        
        return response
    
    async def _record_to_graphiti_safe(
        self,
        request: RetrievalRequest,
        eligibility: float,
        categories: list,
        campaigns: list,
        context_dict: Optional[dict]
    ) -> None:
        """
        Safely record query event to Graphiti.
        
        This method wraps Graphiti recording in try-except to ensure
        that any Graphiti errors don't affect the retrieval pipeline.
        
        Args:
            request: Original retrieval request
            eligibility: Calculated eligibility score
            categories: Extracted categories
            campaigns: Top campaigns returned
            context_dict: User context dictionary
        """
        try:
            # Convert Campaign models to dicts for Graphiti
            campaign_dicts = [
                {
                    "campaign_id": c.campaign_id,
                    "title": c.title,
                    "category": c.category,
                    "relevance_score": c.relevance_score
                }
                for c in campaigns[:10]  # Only record top 10
            ]
            
            await self.graphiti_service.record_query_event(
                query=request.query,
                context=context_dict,
                eligibility=eligibility,
                categories=categories,
                campaigns=campaign_dicts,
                session_id=request.session_id,
                user_id=request.user_id
            )
            
            logger.debug(f"Query event recorded to Graphiti: '{request.query[:50]}...'")
            
        except Exception as e:
            # Log warning but don't propagate error
            logger.warning(f"Graphiti recording failed (non-critical): {e}")
    
    async def _update_profile_safe(
        self,
        request: RetrievalRequest,
        extracted_categories: list,
        context_dict: Optional[dict]
    ) -> None:
        """
        Safely update user profile and trigger analysis.
        
        This method wraps profile updates in try-except to ensure
        that any profile errors don't affect the retrieval pipeline.
        
        Args:
            request: Original retrieval request
            extracted_categories: Categories extracted from query
            context_dict: User context dictionary
        """
        try:
            from src.core.config import settings
            
            # Extract location from context or query
            location = None
            if context_dict and context_dict.get("location"):
                location = context_dict["location"]
            
            # Extract interests from context
            interests = None
            if context_dict and context_dict.get("interests"):
                interests = context_dict["interests"]
            
            # Create or update profile
            profile = await self.profile_repo.create_or_update_profile(
                user_id=request.user_id,
                query=request.query,
                categories=extracted_categories,
                location=location,
                session_id=request.session_id,
                interests=interests
            )
            
            logger.debug(f"Profile updated for user {request.user_id} (query_count={profile.query_count})")
            
            # Trigger profile analysis every N queries
            if self.profile_analyzer and profile.query_count % settings.PROFILE_ANALYSIS_TRIGGER_EVERY_N_QUERIES == 0:
                asyncio.create_task(self._analyze_profile_safe(request.user_id))
                logger.debug(f"Triggered profile analysis for user {request.user_id}")
            
        except Exception as e:
            # Log warning but don't propagate error
            logger.warning(f"Profile update failed (non-critical): {e}")
    
    async def _analyze_profile_safe(self, user_id: str) -> None:
        """
        Safely analyze user profile in background.
        
        Args:
            user_id: User identifier
        """
        try:
            await self.profile_analyzer.analyze_user(user_id)
            logger.debug(f"Profile analysis completed for user {user_id}")
        except Exception as e:
            logger.warning(f"Profile analysis failed (non-critical): {e}")

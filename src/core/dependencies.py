"""Dependency injection for the Ad Retrieval API."""

from functools import lru_cache
from typing import Optional

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
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton repositories (loaded once at startup)
_blocklist_repo: Optional[BlocklistRepository] = None
_taxonomy_repo: Optional[TaxonomyRepository] = None
_vector_repo: Optional[VectorRepository] = None
_campaign_repo: Optional[CampaignRepository] = None
_repositories_initialized = False


async def init_dependencies():
    """
    Initialize all repositories and dependencies at startup.
    
    This function loads:
    - Blocklist repository
    - Taxonomy repository
    - Vector repository (FAISS index)
    - Campaign repository
    
    Called once during FastAPI startup event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _repositories_initialized
    
    if _repositories_initialized:
        logger.warning("Dependencies already initialized")
        return
    
    logger.info("Initializing dependencies...")
    
    try:
        # Initialize repositories
        _blocklist_repo = BlocklistRepository(settings.BLOCKLIST_PATH)
        logger.info("✓ Blocklist repository initialized")
        
        _taxonomy_repo = TaxonomyRepository(settings.TAXONOMY_PATH)
        logger.info("✓ Taxonomy repository initialized")
        
        _vector_repo = VectorRepository(settings.FAISS_INDEX_PATH)
        logger.info("✓ Vector repository initialized")
        
        _campaign_repo = CampaignRepository(settings.CAMPAIGNS_PATH)
        logger.info("✓ Campaign repository initialized")
        
        _repositories_initialized = True
        logger.info("All dependencies initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}", exc_info=True)
        raise


@lru_cache()
def get_retrieval_controller() -> RetrievalController:
    """
    Get the retrieval controller with all dependencies injected.
    
    Uses @lru_cache to ensure singleton behavior - controller is created
    once and reused across requests.
    
    Returns:
        RetrievalController instance
    
    Raises:
        RuntimeError: If dependencies are not initialized
    """
    if not _repositories_initialized:
        raise RuntimeError(
            "Dependencies not initialized. Call init_dependencies() first."
        )
    
    # Initialize services
    eligibility_service = EligibilityService(_blocklist_repo)
    category_service = CategoryService(_taxonomy_repo)
    embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
    search_service = SearchService(_vector_repo, _campaign_repo)
    ranking_service = RankingService()
    
    # Create and return controller
    return RetrievalController(
        eligibility_service=eligibility_service,
        category_service=category_service,
        embedding_service=embedding_service,
        search_service=search_service,
        ranking_service=ranking_service
    )


def get_dependencies_status() -> dict:
    """
    Get the status of dependencies.
    
    Returns:
        Dictionary with initialization status
    """
    return {
        "initialized": _repositories_initialized,
        "repositories": {
            "blocklist": _blocklist_repo is not None,
            "taxonomy": _taxonomy_repo is not None,
            "vector": _vector_repo is not None,
            "campaign": _campaign_repo is not None,
        },
        "stats": {
            "blocklist_size": _blocklist_repo.get_blocklist_size() if _blocklist_repo else 0,
            "taxonomy_categories": _taxonomy_repo.get_category_count() if _taxonomy_repo else 0,
            "vector_index_size": _vector_repo.get_index_size() if _vector_repo else 0,
            "campaign_count": _campaign_repo.get_count() if _campaign_repo else 0,
        } if _repositories_initialized else {}
    }


async def shutdown_dependencies():
    """
    Cleanup dependencies on shutdown.
    
    Called during FastAPI shutdown event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _repositories_initialized
    
    logger.info("Shutting down dependencies...")
    
    # Clear repository references
    _blocklist_repo = None
    _taxonomy_repo = None
    _vector_repo = None
    _campaign_repo = None
    _repositories_initialized = False
    
    # Clear LRU cache
    get_retrieval_controller.cache_clear()
    
    logger.info("Dependencies shut down successfully")

"""Dependency injection for the Ad Retrieval API."""

from functools import lru_cache
from typing import Optional

from src.controllers.retrieval_controller import RetrievalController
from src.services.eligibility_service import EligibilityService
from src.services.category_service import CategoryService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.ranking_service import RankingService
from src.services.graphiti_service import GraphitiService
from src.services.intent_evolution_service import IntentEvolutionService
from src.repositories.blocklist_repository import BlocklistRepository
from src.repositories.taxonomy_repository import TaxonomyRepository
from src.repositories.vector_repository import VectorRepository
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.graphiti_repository import GraphitiRepository
from src.repositories.session_state_repository import SessionStateRepository
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton repositories (loaded once at startup)
_blocklist_repo: Optional[BlocklistRepository] = None
_taxonomy_repo: Optional[TaxonomyRepository] = None
_vector_repo: Optional[VectorRepository] = None
_campaign_repo: Optional[CampaignRepository] = None
_graphiti_repo: Optional[GraphitiRepository] = None
_session_state_repo: Optional[SessionStateRepository] = None
_repositories_initialized = False


async def init_dependencies():
    """
    Initialize all repositories and dependencies at startup.
    
    This function loads:
    - Blocklist repository
    - Taxonomy repository
    - Vector repository (FAISS index)
    - Campaign repository
    - Graphiti repository (optional)
    
    Called once during FastAPI startup event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _graphiti_repo, _session_state_repo, _repositories_initialized
    
    if _repositories_initialized:
        logger.warning("Dependencies already initialized")
        return
    
    logger.info("Initializing dependencies...")
    
    try:
        # Initialize core repositories
        _blocklist_repo = BlocklistRepository(settings.BLOCKLIST_PATH)
        logger.info("✓ Blocklist repository initialized")
        
        _taxonomy_repo = TaxonomyRepository(settings.TAXONOMY_PATH)
        logger.info("✓ Taxonomy repository initialized")
        
        _vector_repo = VectorRepository(settings.FAISS_INDEX_PATH)
        logger.info("✓ Vector repository initialized")
        
        _campaign_repo = CampaignRepository(settings.CAMPAIGNS_PATH)
        logger.info("✓ Campaign repository initialized")
        
        # Initialize session state repository (in-memory, always available)
        _session_state_repo = SessionStateRepository(ttl_minutes=30)
        logger.info("✓ Session state repository initialized")
        
        # Initialize Graphiti (optional - graceful degradation)
        if settings.GRAPHITI_ENABLED:
            try:
                _graphiti_repo = GraphitiRepository(
                    neo4j_uri=settings.GRAPHITI_NEO4J_URI,
                    neo4j_user=settings.GRAPHITI_NEO4J_USER,
                    neo4j_password=settings.GRAPHITI_NEO4J_PASSWORD,
                    openrouter_api_key=settings.OPENROUTER_API_KEY,
                    llm_model=settings.GRAPHITI_LLM_MODEL,
                    namespace=settings.GRAPHITI_NAMESPACE
                )
                await _graphiti_repo.initialize()
                logger.info("✓ Graphiti repository initialized (using OpenRouter)")
            except Exception as e:
                logger.warning(f"Graphiti initialization failed (optional): {e}")
                logger.info("Continuing without Graphiti - system will work normally")
                _graphiti_repo = None
        else:
            logger.info("Graphiti disabled (GRAPHITI_ENABLED=false)")
            _graphiti_repo = None
        
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
    
    # Initialize intent evolution service (optional, requires Graphiti)
    intent_evolution_service = None
    if _graphiti_repo is not None and _graphiti_repo.is_initialized:
        intent_evolution_service = IntentEvolutionService(_graphiti_repo)
        logger.debug("Intent evolution service enabled")
    
    # Initialize ranking service with optional intent evolution
    ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
    
    # Initialize Graphiti service (optional)
    graphiti_service = None
    if _graphiti_repo is not None and _graphiti_repo.is_initialized:
        graphiti_service = GraphitiService(_graphiti_repo)
        logger.debug("Graphiti service enabled for controller")
    
    # Create and return controller
    return RetrievalController(
        eligibility_service=eligibility_service,
        category_service=category_service,
        embedding_service=embedding_service,
        search_service=search_service,
        ranking_service=ranking_service,
        graphiti_service=graphiti_service,
        session_state_repo=_session_state_repo,
        intent_evolution_service=intent_evolution_service
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
            "graphiti": _graphiti_repo is not None and _graphiti_repo.is_initialized,
            "session_state": _session_state_repo is not None,
        },
        "stats": {
            "blocklist_size": _blocklist_repo.get_blocked_terms_count() if _blocklist_repo else 0,
            "taxonomy_categories": _taxonomy_repo.get_category_count() if _taxonomy_repo else 0,
            "vector_index_size": _vector_repo.get_index_size() if _vector_repo else 0,
            "campaign_count": _campaign_repo.get_count() if _campaign_repo else 0,
            "active_sessions": _session_state_repo.get_active_session_count() if _session_state_repo else 0,
        } if _repositories_initialized else {}
    }


async def shutdown_dependencies():
    """
    Cleanup dependencies on shutdown.
    
    Called during FastAPI shutdown event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _graphiti_repo, _session_state_repo, _repositories_initialized
    
    logger.info("Shutting down dependencies...")
    
    # Shutdown Graphiti if initialized
    if _graphiti_repo is not None:
        try:
            await _graphiti_repo.shutdown()
            logger.info("✓ Graphiti repository shut down")
        except Exception as e:
            logger.error(f"Error shutting down Graphiti: {e}")
    
    # Clear session state
    if _session_state_repo is not None:
        try:
            count = _session_state_repo.clear_all_sessions()
            logger.info(f"✓ Session state cleared ({count} sessions)")
        except Exception as e:
            logger.error(f"Error clearing session state: {e}")
    
    # Clear repository references
    _blocklist_repo = None
    _taxonomy_repo = None
    _vector_repo = None
    _campaign_repo = None
    _graphiti_repo = None
    _session_state_repo = None
    _repositories_initialized = False
    
    # Clear LRU cache
    get_retrieval_controller.cache_clear()
    
    logger.info("Dependencies shut down successfully")

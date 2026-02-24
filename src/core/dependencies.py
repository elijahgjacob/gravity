"""Dependency injection for the Ad Retrieval API."""

from functools import lru_cache

from src.controllers.retrieval_controller import RetrievalController
from src.core.config import settings
from src.core.logging_config import get_logger
from src.repositories.blocklist_repository import BlocklistRepository
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.taxonomy_repository import TaxonomyRepository
from src.repositories.vector_repository import VectorRepository
from src.services.category_service import CategoryService
from src.services.eligibility_service import EligibilityService
from src.services.embedding_service import EmbeddingService
from src.services.ranking_service import RankingService
from src.services.search_service import SearchService

try:
    from src.services.graphiti_service import GraphitiService
    from src.repositories.graphiti_repository import GraphitiRepository
except ImportError:
    GraphitiService = None
    GraphitiRepository = None

from src.repositories.profile_repository import ProfileRepository
from src.services.pattern_detector import PatternDetector
from src.services.profile_analyzer import ProfileAnalyzer
from src.services.profile_summary_service import ProfileSummaryService
from src.services.pattern_rules import DEFAULT_RULES, RuleSet
import json
import os

logger = get_logger(__name__)

# Singleton repositories and services (loaded once at startup)
_blocklist_repo: BlocklistRepository | None = None
_taxonomy_repo: TaxonomyRepository | None = None
_vector_repo: VectorRepository | None = None
_campaign_repo: CampaignRepository | None = None
_embedding_service: EmbeddingService | None = None
_graphiti_repo: "GraphitiRepository | None" = None
_profile_repo: ProfileRepository | None = None
_profile_analyzer: ProfileAnalyzer | None = None
_profile_summary_service: ProfileSummaryService | None = None
_repositories_initialized = False


async def init_dependencies():
    """
    Initialize all repositories and dependencies at startup.

    This function loads:
    - Blocklist repository
    - Taxonomy repository
    - Vector repository (FAISS index)
    - Campaign repository
    - Embedding service (loads model at startup to avoid first-request penalty)
    - Graphiti repository (optional)
    - Profile repository and analyzer (optional)
    
    Called once during FastAPI startup event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _embedding_service, _graphiti_repo, _profile_repo, _profile_analyzer
    global _profile_summary_service, _repositories_initialized

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

        _embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
        logger.info("✓ Embedding service initialized")
        
        # Initialize Graphiti (optional - graceful degradation)
        if settings.GRAPHITI_ENABLED and GraphitiRepository is not None:
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
        
        # Initialize Profile Analysis (optional - graceful degradation)
        if settings.PROFILE_ANALYSIS_ENABLED:
            try:
                # Initialize profile repository
                _profile_repo = ProfileRepository(
                    max_size=settings.PROFILE_CACHE_SIZE,
                    ttl_seconds=settings.PROFILE_CACHE_TTL_SECONDS
                )
                logger.info("✓ Profile repository initialized (in-memory cache)")
                
                # Load pattern rules
                rules = DEFAULT_RULES
                if os.path.exists(settings.PATTERN_RULES_PATH):
                    try:
                        with open(settings.PATTERN_RULES_PATH, 'r') as f:
                            rules_data = json.load(f)
                            rule_set = RuleSet(**rules_data)
                            rules = rule_set.get_enabled_rules()
                        logger.info(f"✓ Loaded {len(rules)} pattern rules from {settings.PATTERN_RULES_PATH}")
                    except Exception as e:
                        logger.warning(f"Failed to load pattern rules file: {e}, using defaults")
                else:
                    logger.info(f"✓ Using {len(rules)} default pattern rules")
                
                # Initialize pattern detector
                pattern_detector = PatternDetector(rules)
                
                # Initialize profile analyzer
                _profile_analyzer = ProfileAnalyzer(_profile_repo, pattern_detector)
                logger.info("✓ Profile analyzer initialized")
                
                # Profile summary service (LLM) - only when OpenRouter key is set
                if settings.OPENROUTER_API_KEY:
                    _profile_summary_service = ProfileSummaryService(
                        api_key=settings.OPENROUTER_API_KEY,
                        model=settings.PROFILE_SUMMARY_LLM_MODEL,
                        verify_ssl=settings.OPENROUTER_VERIFY_SSL,
                    )
                    logger.info("✓ Profile summary service initialized (OpenRouter)")
                else:
                    _profile_summary_service = None
                
            except Exception as e:
                logger.warning(f"Profile analysis initialization failed (optional): {e}")
                logger.info("Continuing without profile analysis - system will work normally")
                _profile_repo = None
                _profile_analyzer = None
                _profile_summary_service = None
        else:
            logger.info("Profile analysis disabled (PROFILE_ANALYSIS_ENABLED=false)")
            _profile_repo = None
            _profile_analyzer = None
            _profile_summary_service = None

        _repositories_initialized = True
        logger.info("All dependencies initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}", exc_info=True)
        raise


@lru_cache
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
        raise RuntimeError("Dependencies not initialized. Call init_dependencies() first.")

    # Initialize services (reuse singleton embedding service)
    eligibility_service = EligibilityService(_blocklist_repo)
    category_service = CategoryService(_taxonomy_repo)
    search_service = SearchService(_vector_repo, _campaign_repo)
    ranking_service = RankingService()
    
    # Initialize Graphiti service (optional)
    graphiti_service = None
    if GraphitiService is not None and _graphiti_repo is not None and _graphiti_repo.is_initialized:
        graphiti_service = GraphitiService(_graphiti_repo)
        logger.debug("Graphiti service enabled for controller")

    # Create and return controller
    return RetrievalController(
        eligibility_service=eligibility_service,
        category_service=category_service,
        embedding_service=_embedding_service,
        search_service=search_service,
        ranking_service=ranking_service,
        graphiti_service=graphiti_service,
        profile_repo=_profile_repo,
        profile_analyzer=_profile_analyzer
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
            "profile": _profile_repo is not None,
            "profile_analyzer": _profile_analyzer is not None,
            "profile_summary": _profile_summary_service is not None,
        },
        "stats": (
            {
                "blocklist_size": (
                    _blocklist_repo.get_blocked_terms_count() if _blocklist_repo else 0
                ),
                "taxonomy_categories": _taxonomy_repo.get_category_count() if _taxonomy_repo else 0,
                "vector_index_size": _vector_repo.get_index_size() if _vector_repo else 0,
                "campaign_count": _campaign_repo.get_count() if _campaign_repo else 0,
            }
            if _repositories_initialized
            else {}
        ),
    }


async def shutdown_dependencies():
    """
    Cleanup dependencies on shutdown.

    Called during FastAPI shutdown event.
    """
    global _blocklist_repo, _taxonomy_repo, _vector_repo, _campaign_repo
    global _embedding_service, _graphiti_repo, _profile_repo, _profile_analyzer
    global _repositories_initialized

    logger.info("Shutting down dependencies...")
    
    # Shutdown Graphiti if initialized
    if _graphiti_repo is not None:
        try:
            await _graphiti_repo.shutdown()
            logger.info("✓ Graphiti repository shut down")
        except Exception as e:
            logger.error(f"Error shutting down Graphiti: {e}")

    # Clear repository references
    _blocklist_repo = None
    _taxonomy_repo = None
    _vector_repo = None
    _campaign_repo = None
    _embedding_service = None
    _graphiti_repo = None
    _profile_repo = None
    _profile_analyzer = None
    _profile_summary_service = None
    _repositories_initialized = False

    # Clear LRU cache
    _profile_summary_service = None
    get_retrieval_controller.cache_clear()

    logger.info("Dependencies shut down successfully")


def get_profile_summary_service() -> ProfileSummaryService | None:
    """
    Get the profile summary service (LLM) if available.

    Returns None when OPENROUTER_API_KEY is not set or profile analysis is disabled.
    """
    return _profile_summary_service

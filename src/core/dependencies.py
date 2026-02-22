"""Dependency injection for the Ad Retrieval API."""

from typing import Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Global state for repositories (loaded at startup)
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
    global _repositories_initialized
    
    if _repositories_initialized:
        logger.warning("Dependencies already initialized")
        return
    
    logger.info("Initializing dependencies...")
    
    # TODO: Phase 3-5 will implement actual repository initialization
    # For now, we just mark as initialized
    
    _repositories_initialized = True
    logger.info("Dependencies initialized successfully")


def get_dependencies_status() -> dict:
    """
    Get the status of dependencies.
    
    Returns:
        Dictionary with initialization status
    """
    return {
        "initialized": _repositories_initialized,
        "repositories": {
            "blocklist": _repositories_initialized,
            "taxonomy": _repositories_initialized,
            "vector": _repositories_initialized,
            "campaign": _repositories_initialized,
        }
    }


async def shutdown_dependencies():
    """
    Cleanup dependencies on shutdown.
    
    Called during FastAPI shutdown event.
    """
    global _repositories_initialized
    
    logger.info("Shutting down dependencies...")
    
    # TODO: Phase 3-5 will implement actual cleanup
    
    _repositories_initialized = False
    logger.info("Dependencies shut down successfully")

"""Health check routes."""

from fastapi import APIRouter, Depends, status

from src.api.models.responses import HealthResponse
from src.controllers.retrieval_controller import RetrievalController
from src.core.dependencies import get_dependencies_status, get_retrieval_controller
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the service is running and dependencies are initialized",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Health status and version information
    """
    deps_status = get_dependencies_status()

    if not deps_status["initialized"]:
        logger.warning("Health check: dependencies not initialized")

    return HealthResponse(
        status="healthy" if deps_status["initialized"] else "initializing", version="1.0.0"
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to accept requests",
)
async def readiness_check() -> dict:
    """
    Readiness check endpoint.

    Returns:
        Readiness status with dependency details and statistics
    """
    deps_status = get_dependencies_status()

    return {
        "ready": deps_status["initialized"],
        "dependencies": deps_status["repositories"],
        "stats": deps_status.get("stats", {}),
    }


@router.get(
    "/warmup",
    status_code=status.HTTP_200_OK,
    summary="Warmup endpoint",
    description="Aggressively warm up all models and services to prevent cold starts",
)
async def warmup(controller: RetrievalController = Depends(get_retrieval_controller)) -> dict:
    """
    Warmup endpoint to prevent cold starts.
    
    Aggressively loads ALL models and services:
    - Sentence-transformers embedding model
    - FAISS vector index
    - TF-IDF vectorizer
    - Blocklist and taxonomy
    - All service dependencies
    
    This is called automatically by the frontend on page load.
    
    Returns:
        Warmup status and timing information
    """
    try:
        from src.api.models.requests import RetrievalRequest
        import time
        import asyncio
        
        start_time = time.perf_counter()
        
        # Make 3 concurrent requests to aggressively warm up all code paths
        warmup_queries = [
            "running shoes",  # Trigger embedding + FAISS
            "laptop",         # Different category
            "travel"          # Another category
        ]
        
        tasks = []
        for query in warmup_queries:
            warmup_request = RetrievalRequest(
                query=query,
                context=None,
                user_id=None,  # No user tracking
                session_id=None
            )
            tasks.append(controller.retrieve(warmup_request))
        
        # Execute all warmup requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        warmup_time = (time.perf_counter() - start_time) * 1000
        
        # Check if any failed
        failures = [r for r in results if isinstance(r, Exception)]
        success_count = len(results) - len(failures)
        
        logger.info(f"🔥 Aggressive warmup completed: {success_count}/{len(warmup_queries)} successful in {warmup_time:.2f}ms")
        
        return {
            "status": "warmed_up",
            "warmup_time_ms": round(warmup_time, 2),
            "models_loaded": True,
            "warmup_queries": len(warmup_queries),
            "successful": success_count,
            "message": f"Server fully warmed up with {success_count} test queries"
        }
        
    except Exception as e:
        logger.error(f"❌ Warmup failed: {e}", exc_info=True)
        return {
            "status": "warmup_attempted",
            "models_loaded": False,
            "message": str(e)
        }

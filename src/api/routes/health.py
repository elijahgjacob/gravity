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
    description="Lightweight endpoint to warm up models and prevent cold starts",
)
async def warmup(controller: RetrievalController = Depends(get_retrieval_controller)) -> dict:
    """
    Warmup endpoint to prevent cold starts.
    
    Triggers model loading (embeddings, FAISS index) without requiring user data.
    This is called automatically by the frontend on page load.
    
    Returns:
        Warmup status and timing information
    """
    try:
        from src.api.models.requests import RetrievalRequest
        import time
        
        start_time = time.perf_counter()
        
        # Make a minimal, anonymous request to load all models
        warmup_request = RetrievalRequest(
            query="test",  # Minimal query to trigger model loading
            context=None,
            user_id=None,  # No user tracking
            session_id=None
        )
        
        # Execute retrieval to warm up all services
        _ = await controller.retrieve(warmup_request)
        
        warmup_time = (time.perf_counter() - start_time) * 1000
        
        logger.info(f"Warmup completed in {warmup_time:.2f}ms")
        
        return {
            "status": "warmed_up",
            "warmup_time_ms": round(warmup_time, 2),
            "models_loaded": True,
            "message": "Server is ready for requests"
        }
        
    except Exception as e:
        logger.warning(f"Warmup request failed (non-critical): {e}")
        return {
            "status": "warmup_attempted",
            "models_loaded": False,
            "message": str(e)
        }

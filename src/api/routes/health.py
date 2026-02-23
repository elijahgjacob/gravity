"""Health check routes."""

from fastapi import APIRouter, status

from src.api.models.responses import HealthResponse
from src.core.dependencies import get_dependencies_status
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
        status="healthy" if deps_status["initialized"] else "initializing",
        version="1.0.0"
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
        "stats": deps_status.get("stats", {})
    }

"""Retrieval endpoint routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.models.requests import RetrievalRequest
from src.api.models.responses import RetrievalResponse
from src.controllers.retrieval_controller import RetrievalController
from src.core.dependencies import get_retrieval_controller
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relevant ad campaigns",
    description="""
    Retrieve relevant ad campaigns for a given query.
    
    **Process:**
    1. Scores ad eligibility (0.0-1.0)
    2. Extracts relevant categories (1-10)
    3. Returns top 1000 campaigns by relevance
    
    **Target Latency:** < 100ms (p95)
    """,
    responses={
        200: {
            "description": "Successfully retrieved campaigns",
            "content": {
                "application/json": {
                    "example": {
                        "ad_eligibility": 0.95,
                        "extracted_categories": ["running_shoes", "marathon_gear"],
                        "campaigns": [],
                        "latency_ms": 67.5,
                        "metadata": {},
                    }
                }
            },
        },
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def retrieve_ads(
    request: RetrievalRequest, controller: RetrievalController = Depends(get_retrieval_controller)
) -> RetrievalResponse:
    """
    Retrieve relevant ad campaigns for a user query.

    Args:
        request: Retrieval request with query and optional context
        controller: Injected retrieval controller

    Returns:
        Retrieval response with campaigns and metadata

    Raises:
        HTTPException: If processing fails
    """
    try:
        response = await controller.retrieve(request)
        return response

    except Exception as e:
        logger.error(f"Error processing retrieval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process retrieval request",
        )

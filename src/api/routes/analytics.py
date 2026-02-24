"""Analytics endpoints for profile inference monitoring."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from src.core.dependencies import get_retrieval_controller
from src.controllers.retrieval_controller import RetrievalController
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/profile-stats")
async def get_profile_stats(
    controller: RetrievalController = Depends(get_retrieval_controller)
):
    """
    Get profile system statistics.
    
    Returns:
        Dictionary with profile analysis stats
    """
    if not controller.profile_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Profile analysis not enabled"
        )
    
    try:
        stats = await controller.profile_analyzer.get_analysis_stats()
        return {
            "status": "ok",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get profile stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    controller: RetrievalController = Depends(get_retrieval_controller)
):
    """
    Get profile for a specific user.
    
    Args:
        user_id: User identifier
    
    Returns:
        User profile with query history and inferred intents
    """
    if not controller.profile_repo:
        raise HTTPException(
            status_code=503,
            detail="Profile repository not enabled"
        )
    
    try:
        profile = await controller.profile_repo.get_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile not found for user: {user_id}"
            )
        
        return {
            "status": "ok",
            "profile": profile.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/{user_id}/analyze")
async def trigger_profile_analysis(
    user_id: str,
    controller: RetrievalController = Depends(get_retrieval_controller)
):
    """
    Manually trigger profile analysis for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Updated profile with detected intents
    """
    if not controller.profile_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Profile analyzer not enabled"
        )
    
    try:
        profile = await controller.profile_analyzer.analyze_user(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile not found for user: {user_id}"
            )
        
        return {
            "status": "ok",
            "profile": profile.model_dump(),
            "intents_detected": len(profile.inferred_intents),
            "inferred_categories": profile.inferred_categories
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze profile for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/{user_id}")
async def delete_user_profile(
    user_id: str,
    controller: RetrievalController = Depends(get_retrieval_controller)
):
    """
    Delete a user's profile from cache.
    
    Args:
        user_id: User identifier
    
    Returns:
        Success message
    """
    if not controller.profile_repo:
        raise HTTPException(
            status_code=503,
            detail="Profile repository not enabled"
        )
    
    try:
        await controller.profile_repo.invalidate_profile(user_id)
        return {
            "status": "ok",
            "message": f"Profile deleted for user: {user_id}"
        }
    except Exception as e:
        logger.error(f"Failed to delete profile for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats")
async def get_cache_stats(
    controller: RetrievalController = Depends(get_retrieval_controller)
):
    """
    Get profile cache statistics.
    
    Returns:
        Cache size, utilization, and configuration
    """
    if not controller.profile_repo:
        raise HTTPException(
            status_code=503,
            detail="Profile repository not enabled"
        )
    
    try:
        stats = await controller.profile_repo.get_cache_stats()
        return {
            "status": "ok",
            "cache": stats
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

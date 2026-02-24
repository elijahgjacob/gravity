"""Service for analyzing user query patterns and building profiles."""

from datetime import datetime
from typing import List, Optional
from src.api.models.profiles import UserProfile, InferredIntent
from src.repositories.profile_repository import ProfileRepository
from src.services.pattern_detector import PatternDetector
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ProfileAnalyzer:
    """
    Service for analyzing user query patterns and updating profiles.
    
    Runs asynchronously in background to detect intent patterns
    and update user profiles without impacting retrieval latency.
    """
    
    def __init__(
        self,
        profile_repo: ProfileRepository,
        pattern_detector: PatternDetector
    ):
        """
        Initialize the profile analyzer.
        
        Args:
            profile_repo: Repository for profile storage
            pattern_detector: Service for pattern detection
        """
        self.profile_repo = profile_repo
        self.pattern_detector = pattern_detector
        logger.info("ProfileAnalyzer initialized")
    
    async def analyze_user(self, user_id: str) -> Optional[UserProfile]:
        """
        Analyze a single user's query history and update their profile.
        
        Args:
            user_id: User identifier
        
        Returns:
            Updated UserProfile or None if user not found
        """
        try:
            logger.debug(f"Analyzing user profile: {user_id}")
            
            # Get user profile
            profile = await self.profile_repo.get_profile(user_id)
            if not profile:
                logger.debug(f"No profile found for user: {user_id}")
                return None
            
            # Skip if no query history
            if not profile.query_history:
                logger.debug(f"No query history for user: {user_id}")
                return profile
            
            # Detect patterns
            intents = await self.pattern_detector.detect_patterns(
                query_history=profile.query_history,
                user_id=user_id
            )
            
            # Update profile with new intents
            if intents:
                profile.inferred_intents = intents
                profile.update_inferred_categories()
                await self.profile_repo.save_profile(profile)
                
                logger.info(
                    f"Profile updated for user {user_id}: "
                    f"{len(intents)} intents, {len(profile.inferred_categories)} categories"
                )
            else:
                logger.debug(f"No patterns detected for user: {user_id}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing user {user_id}: {e}")
            return None
    
    async def analyze_batch(self, user_ids: List[str]) -> dict[str, Optional[UserProfile]]:
        """
        Analyze multiple users in batch.
        
        Args:
            user_ids: List of user identifiers
        
        Returns:
            Dictionary mapping user_id to updated profile
        """
        logger.info(f"Batch analyzing {len(user_ids)} users")
        
        results = {}
        for user_id in user_ids:
            profile = await self.analyze_user(user_id)
            results[user_id] = profile
        
        success_count = sum(1 for p in results.values() if p is not None)
        logger.info(f"Batch analysis complete: {success_count}/{len(user_ids)} successful")
        
        return results
    
    async def should_analyze(self, user_id: str, trigger_every_n: int = 5) -> bool:
        """
        Check if user should be analyzed based on query count.
        
        Args:
            user_id: User identifier
            trigger_every_n: Analyze every N queries
        
        Returns:
            True if analysis should be triggered
        """
        profile = await self.profile_repo.get_profile(user_id)
        if not profile:
            return False
        
        # Trigger analysis every N queries
        return profile.query_count % trigger_every_n == 0
    
    async def get_analysis_stats(self) -> dict:
        """
        Get statistics about profile analysis.
        
        Returns:
            Dictionary with analysis stats
        """
        cache_stats = await self.profile_repo.get_cache_stats()
        user_ids = await self.profile_repo.get_all_user_ids()
        
        # Count profiles with intents
        profiles_with_intents = 0
        total_intents = 0
        
        for user_id in user_ids:
            profile = await self.profile_repo.get_profile(user_id)
            if profile and profile.inferred_intents:
                active_intents = profile.get_active_intents()
                if active_intents:
                    profiles_with_intents += 1
                    total_intents += len(active_intents)
        
        return {
            "total_profiles": cache_stats["size"],
            "profiles_with_intents": profiles_with_intents,
            "total_active_intents": total_intents,
            "cache_utilization": cache_stats["utilization"],
            "intent_detection_rate": profiles_with_intents / cache_stats["size"] if cache_stats["size"] > 0 else 0
        }

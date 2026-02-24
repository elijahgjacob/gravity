"""Repository for user profile storage using in-memory cache."""

from datetime import datetime
from typing import List, Optional
from cachetools import TTLCache
from src.api.models.profiles import UserProfile, InferredIntent
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ProfileRepository:
    """
    Repository for user profile storage and retrieval.
    
    Uses in-memory TTL cache for fast profile lookups without external dependencies.
    Profiles automatically expire after TTL period.
    """
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 604800):
        """
        Initialize the profile repository.
        
        Args:
            max_size: Maximum number of profiles to cache (default: 10,000)
            ttl_seconds: Time-to-live for profiles in seconds (default: 7 days)
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.ttl_seconds = ttl_seconds
        logger.info(f"ProfileRepository initialized (max_size={max_size}, ttl={ttl_seconds}s)")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile from cache.
        
        Args:
            user_id: User identifier
        
        Returns:
            UserProfile if found, None otherwise
        """
        profile = self.cache.get(user_id)
        if profile:
            logger.debug(f"Profile cache hit for user: {user_id}")
        else:
            logger.debug(f"Profile cache miss for user: {user_id}")
        return profile
    
    async def save_profile(self, profile: UserProfile) -> None:
        """
        Save user profile to cache.
        
        Args:
            profile: UserProfile to save
        """
        profile.last_updated = datetime.utcnow()
        self.cache[profile.user_id] = profile
        logger.debug(f"Profile saved for user: {profile.user_id} (query_count={profile.query_count})")
    
    async def update_intents(self, user_id: str, intents: List[InferredIntent]) -> None:
        """
        Update inferred intents for a user.
        
        Args:
            user_id: User identifier
            intents: List of inferred intents to set
        """
        profile = await self.get_profile(user_id)
        if profile:
            profile.inferred_intents = intents
            profile.update_inferred_categories()
            await self.save_profile(profile)
            logger.debug(f"Updated intents for user {user_id}: {len(intents)} intents")
        else:
            logger.warning(f"Cannot update intents: profile not found for user {user_id}")
    
    async def get_inferred_categories(self, user_id: str) -> List[str]:
        """
        Get inferred categories for a user (fast lookup).
        
        Args:
            user_id: User identifier
        
        Returns:
            List of inferred categories, empty list if no profile
        """
        profile = await self.get_profile(user_id)
        if profile:
            # Filter expired intents
            active_intents = profile.get_active_intents()
            if len(active_intents) != len(profile.inferred_intents):
                # Update profile to remove expired intents
                profile.inferred_intents = active_intents
                profile.update_inferred_categories()
                await self.save_profile(profile)
            
            return profile.inferred_categories
        return []
    
    async def increment_query_count(self, user_id: str) -> int:
        """
        Increment query count for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            New query count
        """
        profile = await self.get_profile(user_id)
        if profile:
            profile.query_count += 1
            await self.save_profile(profile)
            return profile.query_count
        return 0
    
    async def invalidate_profile(self, user_id: str) -> None:
        """
        Remove profile from cache.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.cache:
            del self.cache[user_id]
            logger.debug(f"Profile invalidated for user: {user_id}")
    
    async def get_all_user_ids(self) -> List[str]:
        """
        Get all cached user IDs.
        
        Returns:
            List of user IDs currently in cache
        """
        return list(self.cache.keys())
    
    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self.cache) / self.cache.maxsize if self.cache.maxsize > 0 else 0
        }
    
    async def create_or_update_profile(
        self,
        user_id: str,
        query: str,
        categories: List[str],
        location: Optional[str] = None,
        session_id: Optional[str] = None,
        interests: Optional[List[str]] = None
    ) -> UserProfile:
        """
        Create new profile or update existing one with new query.
        
        Args:
            user_id: User identifier
            query: Query text
            categories: Extracted categories
            location: Location from query or context
            session_id: Session identifier
            interests: User interests from context
        
        Returns:
            Updated or created UserProfile
        """
        from src.api.models.profiles import QueryHistoryItem
        
        profile = await self.get_profile(user_id)
        
        if profile is None:
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                session_ids=[session_id] if session_id else [],
                query_history=[],
                query_count=0
            )
            logger.info(f"Created new profile for user: {user_id}")
        
        # Add session ID if new
        if session_id and session_id not in profile.session_ids:
            profile.session_ids.append(session_id)
        
        # Add query to history
        query_item = QueryHistoryItem(
            query=query,
            categories=categories,
            timestamp=datetime.utcnow(),
            location=location,
            session_id=session_id
        )
        profile.query_history.append(query_item)
        
        # Keep only last 50 queries
        if len(profile.query_history) > 50:
            profile.query_history = profile.query_history[-50:]
        
        # Update interests
        if interests:
            existing_interests = set(profile.aggregated_interests)
            existing_interests.update(interests)
            profile.aggregated_interests = list(existing_interests)
        
        # Increment query count
        profile.query_count += 1
        
        # Save profile
        await self.save_profile(profile)
        
        return profile

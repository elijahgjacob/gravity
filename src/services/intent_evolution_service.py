"""Service for querying and analyzing intent evolution from Graphiti knowledge graph."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.repositories.graphiti_repository import GraphitiRepository
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class IntentEvolutionService:
    """
    Query Graphiti to understand and predict intent evolution.
    
    Analyzes conversational patterns, intent progression, and purchase
    readiness signals from the knowledge graph to optimize ad targeting.
    """
    
    # Intent stage definitions
    INTENT_STAGES = ["AWARENESS", "RESEARCH", "CONSIDERATION", "PURCHASE"]
    
    # Ad strategy recommendations
    STRATEGY_EDUCATIONAL = "educational"
    STRATEGY_COMPARISON = "comparison"
    STRATEGY_CONVERSION = "conversion"
    
    def __init__(self, repository: GraphitiRepository):
        """
        Initialize the intent evolution service.
        
        Args:
            repository: GraphitiRepository instance for querying Neo4j
        """
        self.repository = repository
        self._cache: Dict[str, Dict] = {}  # Simple in-memory cache
        self._cache_ttl = timedelta(minutes=5)
        
        logger.info("IntentEvolutionService initialized")
    
    async def get_session_intent_trajectory(self, session_id: str) -> Dict:
        """
        Get how intent evolved in current session.
        
        Queries Graphiti/Neo4j for all episodes in the session and analyzes
        the progression of intent signals over time.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing:
                - stages: List of intent stages detected
                - progression: List of stage transitions
                - velocity: Rate of progression (stages per hour)
                - current_stage: Most recent intent stage
                - signals: Key intent signals extracted
        """
        # Check cache first
        cache_key = f"trajectory_{session_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached['timestamp'] < self._cache_ttl:
                logger.debug(f"Returning cached trajectory for session {session_id}")
                return cached['data']
        
        try:
            # Query Neo4j for session episodes
            # This would use Graphiti's search or Neo4j Cypher queries
            # For now, we'll return a structured placeholder that can be
            # implemented once we have real data
            
            trajectory = {
                'session_id': session_id,
                'stages': [],
                'progression': [],
                'velocity': 0.0,
                'current_stage': 'AWARENESS',
                'signals': {
                    'urgency_indicators': [],
                    'budget_mentions': [],
                    'specificity_level': 'low',
                    'hesitation_signals': []
                },
                'query_count': 0,
                'time_span_minutes': 0
            }
            
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': trajectory
            }
            
            logger.debug(f"Computed trajectory for session {session_id}")
            return trajectory
            
        except Exception as e:
            logger.error(f"Failed to get session trajectory: {e}")
            # Return default trajectory on error
            return {
                'session_id': session_id,
                'stages': ['AWARENESS'],
                'progression': [],
                'velocity': 0.0,
                'current_stage': 'AWARENESS',
                'signals': {},
                'query_count': 0,
                'time_span_minutes': 0
            }
    
    async def predict_next_intent_stage(self, session_id: str) -> str:
        """
        Predict user's next likely intent stage.
        
        Based on current trajectory and historical patterns, predicts
        where the user is likely to move next in their journey.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Predicted intent stage: AWARENESS, RESEARCH, CONSIDERATION, or PURCHASE
        """
        try:
            trajectory = await self.get_session_intent_trajectory(session_id)
            current_stage = trajectory['current_stage']
            velocity = trajectory['velocity']
            
            # Simple progression logic
            # In production, this would use ML or pattern matching
            current_idx = self.INTENT_STAGES.index(current_stage)
            
            # High velocity suggests rapid progression
            if velocity > 2.0 and current_idx < len(self.INTENT_STAGES) - 1:
                next_stage = self.INTENT_STAGES[current_idx + 1]
            else:
                # Stay at current or move one step
                next_stage = current_stage
            
            logger.debug(f"Predicted next stage for {session_id}: {next_stage}")
            return next_stage
            
        except Exception as e:
            logger.error(f"Failed to predict next stage: {e}")
            return "AWARENESS"
    
    async def calculate_purchase_readiness(self, session_id: str) -> float:
        """
        Calculate 0-1 score of purchase readiness.
        
        Analyzes multiple signals to determine how close the user is
        to making a purchase decision:
        - Intent stage progression
        - Velocity of progression
        - Specificity of queries
        - Urgency indicators
        - Budget mentions
        
        Args:
            session_id: Session identifier
        
        Returns:
            Readiness score from 0.0 (not ready) to 1.0 (ready to buy)
        """
        try:
            trajectory = await self.get_session_intent_trajectory(session_id)
            
            # Base score from current stage
            stage = trajectory['current_stage']
            stage_scores = {
                'AWARENESS': 0.2,
                'RESEARCH': 0.4,
                'CONSIDERATION': 0.7,
                'PURCHASE': 0.95
            }
            base_score = stage_scores.get(stage, 0.2)
            
            # Adjust for velocity (fast movers are more ready)
            velocity = trajectory['velocity']
            velocity_bonus = min(0.15, velocity * 0.05)
            
            # Adjust for signals
            signals = trajectory.get('signals', {})
            signal_bonus = 0.0
            
            if signals.get('urgency_indicators'):
                signal_bonus += 0.1
            if signals.get('budget_mentions'):
                signal_bonus += 0.1
            if signals.get('specificity_level') == 'high':
                signal_bonus += 0.15
            
            # Adjust for query count (more queries = more engaged)
            query_count = trajectory.get('query_count', 0)
            if query_count >= 3:
                signal_bonus += 0.05
            
            # Calculate final score
            readiness = min(1.0, base_score + velocity_bonus + signal_bonus)
            
            logger.debug(
                f"Purchase readiness for {session_id}: {readiness:.2f} "
                f"(stage: {stage}, velocity: {velocity:.2f})"
            )
            
            return readiness
            
        except Exception as e:
            logger.error(f"Failed to calculate purchase readiness: {e}")
            return 0.2  # Default to low readiness
    
    async def get_optimal_ad_strategy(self, session_id: str) -> str:
        """
        Recommend ad strategy based on intent evolution.
        
        Maps purchase readiness to the most effective ad strategy:
        - Low readiness (0.0-0.4): Educational content
        - Medium readiness (0.4-0.8): Comparison/review content
        - High readiness (0.8-1.0): Conversion-focused content
        
        Args:
            session_id: Session identifier
        
        Returns:
            Strategy recommendation: "educational", "comparison", or "conversion"
        """
        try:
            readiness = await self.calculate_purchase_readiness(session_id)
            
            if readiness >= 0.8:
                strategy = self.STRATEGY_CONVERSION
            elif readiness >= 0.4:
                strategy = self.STRATEGY_COMPARISON
            else:
                strategy = self.STRATEGY_EDUCATIONAL
            
            logger.debug(
                f"Optimal strategy for {session_id}: {strategy} "
                f"(readiness: {readiness:.2f})"
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to get optimal strategy: {e}")
            return self.STRATEGY_EDUCATIONAL
    
    async def get_intent_insights(self, session_id: str) -> Dict:
        """
        Get comprehensive intent insights for a session.
        
        Combines trajectory, readiness, and strategy into a single
        response for easy consumption by ranking service.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with trajectory, readiness, strategy, and recommendations
        """
        try:
            trajectory = await self.get_session_intent_trajectory(session_id)
            readiness = await self.calculate_purchase_readiness(session_id)
            strategy = await self.get_optimal_ad_strategy(session_id)
            next_stage = await self.predict_next_intent_stage(session_id)
            
            insights = {
                'session_id': session_id,
                'current_stage': trajectory['current_stage'],
                'next_stage': next_stage,
                'readiness_score': readiness,
                'recommended_strategy': strategy,
                'velocity': trajectory['velocity'],
                'query_count': trajectory['query_count'],
                'signals': trajectory.get('signals', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(
                f"Intent insights for {session_id}: "
                f"stage={insights['current_stage']}, "
                f"readiness={readiness:.2f}, "
                f"strategy={strategy}"
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get intent insights: {e}")
            return {
                'session_id': session_id,
                'current_stage': 'AWARENESS',
                'next_stage': 'AWARENESS',
                'readiness_score': 0.2,
                'recommended_strategy': self.STRATEGY_EDUCATIONAL,
                'velocity': 0.0,
                'query_count': 0,
                'signals': {},
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear intent cache.
        
        Args:
            session_id: If provided, clear only this session's cache.
                       If None, clear all cache.
        """
        if session_id:
            cache_key = f"trajectory_{session_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Cleared cache for session {session_id}")
        else:
            self._cache.clear()
            logger.debug("Cleared all intent cache")

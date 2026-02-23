"""Service for querying and analyzing intent evolution from Graphiti knowledge graph."""

import re
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
            # Query Neo4j for all episodes in this session
            query = """
            MATCH (e:Episodic)
            WHERE e.name CONTAINS $session_id
            RETURN e.content as content, e.created_at as created_at, e.name as name
            ORDER BY e.created_at ASC
            """
            
            episodes = await self.repository.execute_cypher(
                query, 
                {"session_id": session_id}
            )
            
            if not episodes:
                logger.debug(f"No episodes found for session {session_id}")
                return self._default_trajectory(session_id)
            
            # Parse episodes to extract signals
            stages = []
            urgency_indicators = []
            budget_mentions = []
            specific_products = []
            hesitation_signals = []
            
            for episode in episodes:
                content = episode.get('content', '')
                
                # Extract ad eligibility to determine stage
                eligibility_match = re.search(r'Ad Eligibility:\s*([\d.]+)', content)
                if eligibility_match:
                    eligibility = float(eligibility_match.group(1))
                    
                    # Map eligibility to intent stage
                    if eligibility >= 0.9:
                        stages.append('PURCHASE')
                    elif eligibility >= 0.75:
                        stages.append('CONSIDERATION')
                    elif eligibility >= 0.5:
                        stages.append('RESEARCH')
                    else:
                        stages.append('AWARENESS')
                
                # Extract current query for signal analysis
                query_match = re.search(r'Current Query:\s*"([^"]+)"', content)
                if query_match:
                    query_text = query_match.group(1).lower()
                    
                    # Detect urgency indicators
                    urgency_keywords = ['need', 'urgent', 'today', 'now', 'asap', 'soon', 'immediately']
                    if any(keyword in query_text for keyword in urgency_keywords):
                        urgency_indicators.append(query_text)
                    
                    # Detect budget mentions
                    if re.search(r'\$\d+|under \$|budget|cheap|affordable|value', query_text):
                        budget_mentions.append(query_text)
                    
                    # Detect specific product mentions (brand + model)
                    if re.search(r'(nike|adidas|asics|brooks|hoka|salomon|new balance)\s+\w+\s*\d*', query_text):
                        specific_products.append(query_text)
                    
                    # Detect hesitation signals
                    hesitation_keywords = ['maybe', 'not sure', 'thinking about', 'considering', 'should i']
                    if any(keyword in query_text for keyword in hesitation_keywords):
                        hesitation_signals.append(query_text)
            
            # Calculate specificity level
            specificity_level = 'low'
            if len(specific_products) >= 2:
                specificity_level = 'high'
            elif len(specific_products) >= 1:
                specificity_level = 'medium'
            
            # Calculate velocity (stages per hour)
            velocity = 0.0
            time_span_minutes = 0
            if len(episodes) > 1:
                # Handle Neo4j DateTime objects or ISO strings
                first_created = episodes[0]['created_at']
                last_created = episodes[-1]['created_at']
                
                # Convert to datetime if needed
                if hasattr(first_created, 'to_native'):
                    # Neo4j DateTime object
                    first_time = first_created.to_native()
                    last_time = last_created.to_native()
                elif isinstance(first_created, str):
                    # ISO string
                    first_time = datetime.fromisoformat(first_created.replace('Z', '+00:00'))
                    last_time = datetime.fromisoformat(last_created.replace('Z', '+00:00'))
                else:
                    # Already datetime
                    first_time = first_created
                    last_time = last_created
                
                time_span = (last_time - first_time).total_seconds()
                time_span_minutes = time_span / 60
                
                # Calculate unique stages
                unique_stages = len(set(stages))
                if time_span > 0:
                    velocity = (unique_stages / (time_span / 3600))  # stages per hour
            
            # Calculate progression (stage transitions)
            progression = []
            for i in range(1, len(stages)):
                if stages[i] != stages[i-1]:
                    progression.append({
                        'from': stages[i-1],
                        'to': stages[i],
                        'query_number': i + 1
                    })
            
            trajectory = {
                'session_id': session_id,
                'stages': stages,
                'progression': progression,
                'velocity': round(velocity, 2),
                'current_stage': stages[-1] if stages else 'AWARENESS',
                'signals': {
                    'urgency_indicators': urgency_indicators,
                    'budget_mentions': budget_mentions,
                    'specificity_level': specificity_level,
                    'specific_products': specific_products,
                    'hesitation_signals': hesitation_signals
                },
                'query_count': len(episodes),
                'time_span_minutes': round(time_span_minutes, 2)
            }
            
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': trajectory
            }
            
            logger.debug(
                f"Computed trajectory for {session_id}: "
                f"{len(episodes)} queries, stage={trajectory['current_stage']}, "
                f"velocity={velocity:.2f}"
            )
            return trajectory
            
        except Exception as e:
            logger.error(f"Failed to get session trajectory: {e}", exc_info=True)
            return self._default_trajectory(session_id)
    
    def _default_trajectory(self, session_id: str) -> Dict:
        """Return default trajectory when no data available."""
        return {
            'session_id': session_id,
            'stages': ['AWARENESS'],
            'progression': [],
            'velocity': 0.0,
            'current_stage': 'AWARENESS',
            'signals': {
                'urgency_indicators': [],
                'budget_mentions': [],
                'specificity_level': 'low',
                'specific_products': [],
                'hesitation_signals': []
            },
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

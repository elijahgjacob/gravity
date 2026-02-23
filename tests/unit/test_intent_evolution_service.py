"""Unit tests for IntentEvolutionService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.services.intent_evolution_service import IntentEvolutionService
from src.repositories.graphiti_repository import GraphitiRepository


class TestIntentEvolutionService:
    """Test intent evolution service functionality."""
    
    @pytest.fixture
    def mock_graphiti_repo(self):
        """Create a mock Graphiti repository."""
        repo = Mock(spec=GraphitiRepository)
        repo.is_initialized = True
        return repo
    
    @pytest.fixture
    def service(self, mock_graphiti_repo):
        """Create IntentEvolutionService with mocked repository."""
        return IntentEvolutionService(mock_graphiti_repo)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service can be initialized."""
        assert service is not None
        assert service.repository is not None
        assert service._cache == {}
    
    @pytest.mark.asyncio
    async def test_get_session_intent_trajectory_returns_structure(self, service):
        """Test trajectory returns expected structure."""
        trajectory = await service.get_session_intent_trajectory("test_session")
        
        assert 'session_id' in trajectory
        assert 'stages' in trajectory
        assert 'progression' in trajectory
        assert 'velocity' in trajectory
        assert 'current_stage' in trajectory
        assert 'signals' in trajectory
        assert 'query_count' in trajectory
        assert 'time_span_minutes' in trajectory
    
    @pytest.mark.asyncio
    async def test_get_session_intent_trajectory_caching(self, service):
        """Test trajectory results are cached."""
        session_id = "test_session"
        
        # First call
        trajectory1 = await service.get_session_intent_trajectory(session_id)
        
        # Second call (should be cached)
        trajectory2 = await service.get_session_intent_trajectory(session_id)
        
        # Should return same object (from cache)
        assert trajectory1 == trajectory2
        assert f"trajectory_{session_id}" in service._cache
    
    @pytest.mark.asyncio
    async def test_calculate_purchase_readiness_awareness_stage(self, service):
        """Test low readiness for AWARENESS stage."""
        # Mock trajectory with AWARENESS stage
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.return_value = {
                'current_stage': 'AWARENESS',
                'velocity': 0.0,
                'signals': {},
                'query_count': 1
            }
            
            readiness = await service.calculate_purchase_readiness("test_session")
            
            # AWARENESS stage should have low readiness (0.2 base)
            assert 0.0 <= readiness <= 0.5
            assert readiness < 0.4  # Should be in "educational" range
    
    @pytest.mark.asyncio
    async def test_calculate_purchase_readiness_purchase_stage(self, service):
        """Test high readiness for PURCHASE stage."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.return_value = {
                'current_stage': 'PURCHASE',
                'velocity': 2.0,
                'signals': {
                    'urgency_indicators': ['need now', 'urgent'],
                    'budget_mentions': ['$150'],
                    'specificity_level': 'high'
                },
                'query_count': 5
            }
            
            readiness = await service.calculate_purchase_readiness("test_session")
            
            # PURCHASE stage with signals should have high readiness
            assert readiness >= 0.8
            assert readiness <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_purchase_readiness_consideration_stage(self, service):
        """Test medium readiness for CONSIDERATION stage."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.return_value = {
                'current_stage': 'CONSIDERATION',
                'velocity': 1.0,
                'signals': {
                    'budget_mentions': ['under $200']
                },
                'query_count': 3
            }
            
            readiness = await service.calculate_purchase_readiness("test_session")
            
            # CONSIDERATION stage should have medium readiness
            assert 0.4 <= readiness <= 0.9
    
    @pytest.mark.asyncio
    async def test_calculate_purchase_readiness_with_velocity_bonus(self, service):
        """Test velocity increases readiness."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            # Low velocity
            mock_traj.return_value = {
                'current_stage': 'RESEARCH',
                'velocity': 0.0,
                'signals': {},
                'query_count': 2
            }
            readiness_low_velocity = await service.calculate_purchase_readiness("session1")
            
            # High velocity
            mock_traj.return_value = {
                'current_stage': 'RESEARCH',
                'velocity': 3.0,
                'signals': {},
                'query_count': 2
            }
            readiness_high_velocity = await service.calculate_purchase_readiness("session2")
            
            # High velocity should increase readiness
            assert readiness_high_velocity > readiness_low_velocity
    
    @pytest.mark.asyncio
    async def test_calculate_purchase_readiness_error_handling(self, service):
        """Test readiness calculation handles errors gracefully."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.side_effect = Exception("Neo4j connection error")
            
            readiness = await service.calculate_purchase_readiness("test_session")
            
            # Should return default low readiness on error
            assert readiness == 0.2
    
    @pytest.mark.asyncio
    async def test_predict_next_intent_stage_progression(self, service):
        """Test stage prediction based on velocity."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            # High velocity from AWARENESS
            mock_traj.return_value = {
                'current_stage': 'AWARENESS',
                'velocity': 3.0,
                'signals': {},
                'query_count': 3
            }
            
            next_stage = await service.predict_next_intent_stage("test_session")
            
            # High velocity should predict progression
            assert next_stage in service.INTENT_STAGES
    
    @pytest.mark.asyncio
    async def test_predict_next_intent_stage_at_final_stage(self, service):
        """Test prediction when already at PURCHASE stage."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.return_value = {
                'current_stage': 'PURCHASE',
                'velocity': 1.0,
                'signals': {},
                'query_count': 5
            }
            
            next_stage = await service.predict_next_intent_stage("test_session")
            
            # Should stay at PURCHASE (can't progress further)
            assert next_stage == 'PURCHASE'
    
    @pytest.mark.asyncio
    async def test_get_optimal_ad_strategy_high_readiness(self, service):
        """Test conversion strategy for high readiness."""
        with patch.object(service, 'calculate_purchase_readiness', new_callable=AsyncMock) as mock_readiness:
            mock_readiness.return_value = 0.9
            
            strategy = await service.get_optimal_ad_strategy("test_session")
            
            assert strategy == service.STRATEGY_CONVERSION
    
    @pytest.mark.asyncio
    async def test_get_optimal_ad_strategy_low_readiness(self, service):
        """Test educational strategy for low readiness."""
        with patch.object(service, 'calculate_purchase_readiness', new_callable=AsyncMock) as mock_readiness:
            mock_readiness.return_value = 0.2
            
            strategy = await service.get_optimal_ad_strategy("test_session")
            
            assert strategy == service.STRATEGY_EDUCATIONAL
    
    @pytest.mark.asyncio
    async def test_get_optimal_ad_strategy_medium_readiness(self, service):
        """Test comparison strategy for medium readiness."""
        with patch.object(service, 'calculate_purchase_readiness', new_callable=AsyncMock) as mock_readiness:
            mock_readiness.return_value = 0.6
            
            strategy = await service.get_optimal_ad_strategy("test_session")
            
            assert strategy == service.STRATEGY_COMPARISON
    
    @pytest.mark.asyncio
    async def test_get_optimal_ad_strategy_error_handling(self, service):
        """Test strategy recommendation handles errors gracefully."""
        with patch.object(service, 'calculate_purchase_readiness', new_callable=AsyncMock) as mock_readiness:
            mock_readiness.side_effect = Exception("Error")
            
            strategy = await service.get_optimal_ad_strategy("test_session")
            
            # Should return default educational strategy on error
            assert strategy == service.STRATEGY_EDUCATIONAL
    
    @pytest.mark.asyncio
    async def test_get_intent_insights_comprehensive(self, service):
        """Test comprehensive intent insights."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj, \
             patch.object(service, 'calculate_purchase_readiness', new_callable=AsyncMock) as mock_readiness, \
             patch.object(service, 'get_optimal_ad_strategy', new_callable=AsyncMock) as mock_strategy, \
             patch.object(service, 'predict_next_intent_stage', new_callable=AsyncMock) as mock_next:
            
            mock_traj.return_value = {
                'current_stage': 'CONSIDERATION',
                'velocity': 1.5,
                'query_count': 3,
                'signals': {'budget_mentions': ['$100']}
            }
            mock_readiness.return_value = 0.7
            mock_strategy.return_value = 'comparison'
            mock_next.return_value = 'PURCHASE'
            
            insights = await service.get_intent_insights("test_session")
            
            assert insights['session_id'] == "test_session"
            assert insights['current_stage'] == 'CONSIDERATION'
            assert insights['next_stage'] == 'PURCHASE'
            assert insights['readiness_score'] == 0.7
            assert insights['recommended_strategy'] == 'comparison'
            assert 'velocity' in insights
            assert 'query_count' in insights
            assert 'signals' in insights
            assert 'timestamp' in insights
    
    @pytest.mark.asyncio
    async def test_get_intent_insights_error_handling(self, service):
        """Test insights return defaults on error."""
        with patch.object(service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.side_effect = Exception("Error")
            
            insights = await service.get_intent_insights("test_session")
            
            # Should return default insights on error
            assert insights['session_id'] == "test_session"
            assert insights['current_stage'] == 'AWARENESS'
            assert insights['readiness_score'] == 0.2
            assert insights['recommended_strategy'] == service.STRATEGY_EDUCATIONAL
    
    def test_clear_cache_specific_session(self, service):
        """Test clearing cache for specific session."""
        # Add to cache
        service._cache['trajectory_session1'] = {'timestamp': datetime.now(), 'data': {}}
        service._cache['trajectory_session2'] = {'timestamp': datetime.now(), 'data': {}}
        
        # Clear specific session
        service.clear_cache('session1')
        
        assert 'trajectory_session1' not in service._cache
        assert 'trajectory_session2' in service._cache
    
    def test_clear_cache_all(self, service):
        """Test clearing all cache."""
        # Add to cache
        service._cache['trajectory_session1'] = {'timestamp': datetime.now(), 'data': {}}
        service._cache['trajectory_session2'] = {'timestamp': datetime.now(), 'data': {}}
        
        # Clear all
        service.clear_cache()
        
        assert len(service._cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, service):
        """Test cache expires after TTL."""
        session_id = "test_session"
        
        # Get trajectory (adds to cache)
        await service.get_session_intent_trajectory(session_id)
        
        # Manually expire cache entry
        cache_key = f"trajectory_{session_id}"
        service._cache[cache_key]['timestamp'] = datetime.now() - timedelta(minutes=10)
        
        # Next call should not use expired cache
        # (In real implementation, this would fetch fresh data)
        trajectory = await service.get_session_intent_trajectory(session_id)
        
        # Verify cache was updated with fresh timestamp
        assert (datetime.now() - service._cache[cache_key]['timestamp']).total_seconds() < 5

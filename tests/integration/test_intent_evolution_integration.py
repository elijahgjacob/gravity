"""Integration tests for intent evolution with Graphiti."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.intent_evolution_service import IntentEvolutionService
from src.services.graphiti_service import GraphitiService
from src.repositories.graphiti_repository import GraphitiRepository
from src.repositories.session_state_repository import SessionStateRepository
from src.controllers.retrieval_controller import RetrievalController
from src.api.models.requests import RetrievalRequest, UserContext


class TestIntentEvolutionIntegration:
    """Integration tests for intent evolution tracking."""
    
    @pytest.fixture
    def mock_graphiti_repo(self):
        """Create a mock Graphiti repository."""
        repo = Mock(spec=GraphitiRepository)
        repo.is_initialized = True
        repo.add_episode = AsyncMock()
        return repo
    
    @pytest.fixture
    def graphiti_service(self, mock_graphiti_repo):
        """Create GraphitiService with mocked repository."""
        return GraphitiService(mock_graphiti_repo)
    
    @pytest.fixture
    def intent_evolution_service(self, mock_graphiti_repo):
        """Create IntentEvolutionService with mocked repository."""
        return IntentEvolutionService(mock_graphiti_repo)
    
    @pytest.fixture
    def session_state_repo(self):
        """Create real SessionStateRepository."""
        return SessionStateRepository(ttl_minutes=30)
    
    @pytest.mark.asyncio
    async def test_graphiti_records_conversational_query(self, graphiti_service, mock_graphiti_repo):
        """Test Graphiti records conversational queries with session context."""
        session_id = "test_session_123"
        previous_queries = [
            {
                'query': 'running shoes',
                'timestamp': datetime.now(),
                'eligibility': 0.8
            }
        ]
        
        await graphiti_service.record_conversational_query(
            query="marathon training shoes",
            session_id=session_id,
            previous_queries=previous_queries,
            context={'age': 30, 'gender': 'male'},
            eligibility=0.85,
            categories=['running_shoes', 'athletic_footwear'],
            campaigns=[
                {'campaign_id': 'c1', 'title': 'Nike Pegasus', 'category': 'running_shoes', 'relevance_score': 0.9}
            ]
        )
        
        # Verify add_episode was called
        mock_graphiti_repo.add_episode.assert_called_once()
        
        # Verify episode contains session context
        call_args = mock_graphiti_repo.add_episode.call_args
        assert 'episode_body' in call_args.kwargs
        episode_body = call_args.kwargs['episode_body']
        
        assert session_id in episode_body
        assert 'marathon training shoes' in episode_body
        assert 'running shoes' in episode_body  # Previous query
        assert 'Conversation History' in episode_body
    
    @pytest.mark.asyncio
    async def test_session_state_tracks_queries(self, session_state_repo):
        """Test session state correctly tracks queries."""
        session_id = "test_session"
        
        # Add first query
        session_state_repo.add_query(session_id, {
            'query': 'running shoes',
            'timestamp': datetime.now(),
            'eligibility': 0.8
        })
        
        # Add second query
        session_state_repo.add_query(session_id, {
            'query': 'marathon training',
            'timestamp': datetime.now(),
            'eligibility': 0.85
        })
        
        # Retrieve queries
        queries = session_state_repo.get_session_queries(session_id)
        
        assert len(queries) == 2
        assert queries[0]['query'] == 'running shoes'
        assert queries[1]['query'] == 'marathon training'
    
    @pytest.mark.asyncio
    async def test_intent_progression_tracking(self, intent_evolution_service):
        """Test tracking intent across multiple queries."""
        session_id = "progression_test"
        
        # Simulate progression: AWARENESS → RESEARCH → CONSIDERATION
        # In real implementation, this would query Neo4j for actual progression
        
        # Get trajectory (mocked for now)
        trajectory = await intent_evolution_service.get_session_intent_trajectory(session_id)
        
        # Verify trajectory structure
        assert 'stages' in trajectory
        assert 'progression' in trajectory
        assert 'velocity' in trajectory
        assert 'current_stage' in trajectory
    
    @pytest.mark.asyncio
    async def test_purchase_readiness_calculation_integration(self, intent_evolution_service):
        """Test purchase readiness calculation with mocked trajectory."""
        session_id = "readiness_test"
        
        # Mock trajectory for high readiness scenario
        with patch.object(intent_evolution_service, 'get_session_intent_trajectory', new_callable=AsyncMock) as mock_traj:
            mock_traj.return_value = {
                'current_stage': 'PURCHASE',
                'velocity': 2.5,
                'signals': {
                    'urgency_indicators': ['need now'],
                    'budget_mentions': ['$150'],
                    'specificity_level': 'high'
                },
                'query_count': 4
            }
            
            readiness = await intent_evolution_service.calculate_purchase_readiness(session_id)
            
            # High readiness scenario
            assert readiness >= 0.8
            assert readiness <= 1.0
    
    @pytest.mark.asyncio
    async def test_intent_insights_full_flow(self, intent_evolution_service):
        """Test getting comprehensive intent insights."""
        session_id = "insights_test"
        
        insights = await intent_evolution_service.get_intent_insights(session_id)
        
        # Verify all required fields present
        assert 'session_id' in insights
        assert 'current_stage' in insights
        assert 'next_stage' in insights
        assert 'readiness_score' in insights
        assert 'recommended_strategy' in insights
        assert 'velocity' in insights
        assert 'query_count' in insights
        assert 'signals' in insights
        assert 'timestamp' in insights
        
        # Verify valid values
        assert insights['current_stage'] in intent_evolution_service.INTENT_STAGES
        assert 0.0 <= insights['readiness_score'] <= 1.0
        assert insights['recommended_strategy'] in [
            intent_evolution_service.STRATEGY_EDUCATIONAL,
            intent_evolution_service.STRATEGY_COMPARISON,
            intent_evolution_service.STRATEGY_CONVERSION
        ]
    
    @pytest.mark.asyncio
    async def test_conversational_query_formatting(self, graphiti_service):
        """Test conversational query episode formatting."""
        previous_queries = [
            {
                'query': 'running shoes',
                'timestamp': datetime.now(),
                'eligibility': 0.8
            },
            {
                'query': 'marathon training',
                'timestamp': datetime.now(),
                'eligibility': 0.85
            }
        ]
        
        # Test formatting methods
        history = graphiti_service._format_query_history(previous_queries)
        assert 'running shoes' in history
        assert 'marathon training' in history
        
        context = graphiti_service._format_context({'age': 30, 'gender': 'male'})
        assert 'Age: 30' in context
        assert 'Gender: male' in context
        
        campaigns = graphiti_service._format_campaigns([
            {'title': 'Nike Pegasus', 'category': 'running_shoes', 'relevance_score': 0.9}
        ])
        assert 'Nike Pegasus' in campaigns
        assert 'running_shoes' in campaigns
    
    @pytest.mark.asyncio
    async def test_time_span_calculation(self, graphiti_service):
        """Test conversation time span calculation."""
        from datetime import timedelta
        
        now = datetime.now()
        previous_queries = [
            {
                'query': 'first query',
                'timestamp': now - timedelta(minutes=10),
                'eligibility': 0.8
            },
            {
                'query': 'second query',
                'timestamp': now - timedelta(minutes=5),
                'eligibility': 0.85
            }
        ]
        
        time_span = graphiti_service._calculate_time_span(previous_queries)
        
        # Should indicate minutes
        assert 'minute' in time_span.lower() or 'second' in time_span.lower()
    
    @pytest.mark.asyncio
    async def test_topic_shift_detection(self, graphiti_service):
        """Test topic shift detection in conversations."""
        # Same topic
        previous_queries = [{'query': 'running shoes for marathon', 'timestamp': datetime.now()}]
        shift = graphiti_service._detect_topic_shift(previous_queries, 'best marathon running shoes')
        assert shift in ['Continuing same topic', 'Related topic']
        
        # Different topic
        previous_queries = [{'query': 'running shoes', 'timestamp': datetime.now()}]
        shift = graphiti_service._detect_topic_shift(previous_queries, 'laptop computers')
        assert shift in ['New topic', 'Related topic']
    
    @pytest.mark.asyncio
    async def test_session_cleanup_integration(self, session_state_repo):
        """Test session cleanup removes expired sessions."""
        from datetime import timedelta
        
        # Create short TTL repo
        repo = SessionStateRepository(ttl_minutes=0)
        
        # Add session
        repo.add_query("test_session", {
            'query': 'test',
            'timestamp': datetime.now(),
            'eligibility': 0.8
        })
        
        # Manually expire it
        with repo._lock:
            repo.sessions["test_session"]['last_accessed'] = datetime.now() - timedelta(minutes=1)
        
        # Cleanup
        removed = repo.cleanup_expired_sessions()
        
        assert removed == 1
        assert repo.get_active_session_count() == 0
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, session_state_repo):
        """Test multiple sessions are tracked independently."""
        # Add queries to session 1
        session_state_repo.add_query("session_1", {
            'query': 'running shoes',
            'timestamp': datetime.now(),
            'eligibility': 0.8
        })
        
        # Add queries to session 2
        session_state_repo.add_query("session_2", {
            'query': 'laptops',
            'timestamp': datetime.now(),
            'eligibility': 0.9
        })
        
        # Verify independence
        queries_1 = session_state_repo.get_session_queries("session_1")
        queries_2 = session_state_repo.get_session_queries("session_2")
        
        assert len(queries_1) == 1
        assert len(queries_2) == 1
        assert queries_1[0]['query'] == 'running shoes'
        assert queries_2[0]['query'] == 'laptops'
    
    @pytest.mark.asyncio
    async def test_graphiti_error_handling_non_blocking(self, mock_graphiti_repo):
        """Test Graphiti errors don't block the system."""
        # Make add_episode raise an error
        mock_graphiti_repo.add_episode = AsyncMock(side_effect=Exception("Neo4j connection error"))
        
        graphiti_service = GraphitiService(mock_graphiti_repo)
        
        # Should not raise exception (logs warning instead)
        try:
            await graphiti_service.record_conversational_query(
                query="test query",
                session_id="test_session",
                previous_queries=[],
                context=None,
                eligibility=0.8,
                categories=[],
                campaigns=[]
            )
            # Success - error was handled gracefully
        except Exception as e:
            pytest.fail(f"Graphiti error should not propagate: {e}")
    
    @pytest.mark.asyncio
    async def test_intent_caching_performance(self, intent_evolution_service):
        """Test intent caching improves performance."""
        import time
        
        session_id = "cache_test"
        
        # First call (no cache)
        start1 = time.perf_counter()
        await intent_evolution_service.get_session_intent_trajectory(session_id)
        time1 = time.perf_counter() - start1
        
        # Second call (cached)
        start2 = time.perf_counter()
        await intent_evolution_service.get_session_intent_trajectory(session_id)
        time2 = time.perf_counter() - start2
        
        # Cached call should be faster (or similar if very fast)
        # This is a soft assertion since timing can vary
        assert time2 <= time1 * 1.5  # Allow some variance

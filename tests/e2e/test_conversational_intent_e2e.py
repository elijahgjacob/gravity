"""End-to-end tests for conversational intent evolution."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.controllers.retrieval_controller import RetrievalController
from src.services.eligibility_service import EligibilityService
from src.services.category_service import CategoryService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.ranking_service import RankingService
from src.services.graphiti_service import GraphitiService
from src.services.intent_evolution_service import IntentEvolutionService
from src.repositories.session_state_repository import SessionStateRepository
from src.api.models.requests import RetrievalRequest, UserContext


class TestConversationalIntentE2E:
    """End-to-end tests for full conversation flow with intent evolution."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mocked services for E2E testing."""
        eligibility_service = Mock(spec=EligibilityService)
        eligibility_service.score = AsyncMock(return_value=(0.8, None))
        
        category_service = Mock(spec=CategoryService)
        category_service.extract = AsyncMock(return_value=['running_shoes', 'athletic_footwear'])
        
        embedding_service = Mock(spec=EmbeddingService)
        embedding_service.embed_query = AsyncMock(return_value=[0.1] * 384)
        
        # Mock search service with varied campaigns
        def create_campaigns(query):
            campaigns = []
            for i in range(50):
                campaigns.append({
                    'campaign_id': f'c{i}',
                    'title': f'Running Shoe Campaign {i}',
                    'category': 'running_shoes',
                    'similarity_score': 0.9 - (i * 0.01),
                    'description': 'High-quality running shoes',
                    'keywords': ['running', 'shoes', 'athletic']
                })
            return campaigns
        
        search_service = Mock(spec=SearchService)
        search_service.search = AsyncMock(side_effect=lambda emb, k: create_campaigns(None))
        
        return {
            'eligibility': eligibility_service,
            'category': category_service,
            'embedding': embedding_service,
            'search': search_service
        }
    
    @pytest.fixture
    def full_controller(self, mock_services):
        """Create fully configured controller with all intent features."""
        session_state_repo = SessionStateRepository(ttl_minutes=30)
        
        mock_graphiti_repo = Mock()
        mock_graphiti_repo.is_initialized = True
        mock_graphiti_repo.add_episode = AsyncMock()
        
        graphiti_service = GraphitiService(mock_graphiti_repo)
        intent_evolution_service = IntentEvolutionService(mock_graphiti_repo)
        ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
        
        return RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            graphiti_service=graphiti_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, full_controller):
        """Test complete conversation with intent evolution."""
        session_id = "e2e_test_session_123"
        
        # Message 1: "I'm thinking about running shoes"
        request1 = RetrievalRequest(
            query="I'm thinking about running shoes",
            context=UserContext(age=30, gender="male"),
            session_id=session_id
        )
        
        response1 = await full_controller.retrieve(request1)
        
        assert response1.ad_eligibility > 0.0
        assert len(response1.campaigns) > 0
        assert response1.latency_ms < 100
        
        # Message 2: "I need them for marathon training"
        request2 = RetrievalRequest(
            query="I need them for marathon training",
            context=UserContext(age=30, gender="male"),
            session_id=session_id
        )
        
        response2 = await full_controller.retrieve(request2)
        
        assert response2.ad_eligibility > 0.0
        assert len(response2.campaigns) > 0
        assert response2.latency_ms < 100
        
        # Message 3: "What's the best value under $150?"
        request3 = RetrievalRequest(
            query="What's the best value under $150?",
            context=UserContext(age=30, gender="male"),
            session_id=session_id
        )
        
        response3 = await full_controller.retrieve(request3)
        
        assert response3.ad_eligibility > 0.0
        assert len(response3.campaigns) > 0
        assert response3.latency_ms < 100
        
        # Verify session state tracked all queries
        session_queries = full_controller.session_state_repo.get_session_queries(session_id)
        assert len(session_queries) == 3
        assert session_queries[0]['query'] == "I'm thinking about running shoes"
        assert session_queries[1]['query'] == "I need them for marathon training"
        assert session_queries[2]['query'] == "What's the best value under $150?"
        
        # Verify Graphiti recorded all queries
        assert full_controller.graphiti_service.repository.add_episode.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_intent_improves_relevance_over_conversation(self, full_controller):
        """Test that intent tracking improves relevance through conversation."""
        session_id = "relevance_test_session"
        
        queries = [
            "running shoes",
            "marathon training shoes",
            "best marathon shoes under $150",
            "where to buy Nike Pegasus 40"
        ]
        
        responses = []
        for query in queries:
            request = RetrievalRequest(
                query=query,
                context=UserContext(age=30, gender="male"),
                session_id=session_id
            )
            response = await full_controller.retrieve(request)
            responses.append(response)
        
        # All responses should be successful
        assert all(r.ad_eligibility > 0.0 for r in responses)
        assert all(len(r.campaigns) > 0 for r in responses)
        assert all(r.latency_ms < 100 for r in responses)
        
        # Session should have all 4 queries
        session_queries = full_controller.session_state_repo.get_session_queries(session_id)
        assert len(session_queries) == 4
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, full_controller):
        """Test multiple sessions are tracked independently."""
        # Session 1: Running shoes
        session1_id = "session_1"
        request1 = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id=session1_id
        )
        await full_controller.retrieve(request1)
        
        # Session 2: Laptops
        session2_id = "session_2"
        request2 = RetrievalRequest(
            query="laptops",
            context=UserContext(age=25, gender="female"),
            session_id=session2_id
        )
        await full_controller.retrieve(request2)
        
        # Verify sessions are independent
        queries1 = full_controller.session_state_repo.get_session_queries(session1_id)
        queries2 = full_controller.session_state_repo.get_session_queries(session2_id)
        
        assert len(queries1) == 1
        assert len(queries2) == 1
        assert queries1[0]['query'] == "running shoes"
        assert queries2[0]['query'] == "laptops"
    
    @pytest.mark.asyncio
    async def test_conversation_without_session_id_works(self, full_controller):
        """Test system works normally without session_id."""
        request = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male")
            # No session_id
        )
        
        response = await full_controller.retrieve(request)
        
        # Should work normally
        assert response.ad_eligibility > 0.0
        assert len(response.campaigns) > 0
        assert response.latency_ms < 100
    
    @pytest.mark.asyncio
    async def test_graphiti_records_with_session_context(self, full_controller):
        """Test Graphiti records include full session context."""
        session_id = "graphiti_context_test"
        
        # First query
        request1 = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id=session_id
        )
        await full_controller.retrieve(request1)
        
        # Second query (should include first query in context)
        request2 = RetrievalRequest(
            query="marathon training",
            context=UserContext(age=30, gender="male"),
            session_id=session_id
        )
        await full_controller.retrieve(request2)
        
        # Give async tasks time to complete
        await asyncio.sleep(0.1)
        
        # Verify Graphiti was called with conversational context
        assert full_controller.graphiti_service.repository.add_episode.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_all_responses_under_100ms(self, full_controller):
        """Test all responses in conversation stay under 100ms."""
        session_id = "latency_test_session"
        
        queries = [
            "running shoes",
            "marathon training shoes",
            "best value running shoes",
            "Nike Pegasus 40",
            "where to buy running shoes"
        ]
        
        for query in queries:
            request = RetrievalRequest(
                query=query,
                context=UserContext(age=30, gender="male"),
                session_id=session_id
            )
            
            response = await full_controller.retrieve(request)
            
            # CRITICAL: Every response must be under 100ms
            assert response.latency_ms < 100, \
                f"Query '{query}' exceeded 100ms: {response.latency_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_session_info_tracking(self, full_controller):
        """Test session info is correctly tracked."""
        session_id = "info_test_session"
        
        # Add multiple queries
        for i in range(5):
            request = RetrievalRequest(
                query=f"running shoes query {i}",
                context=UserContext(age=30, gender="male"),
                session_id=session_id
            )
            await full_controller.retrieve(request)
        
        # Get session info
        session_info = full_controller.session_state_repo.get_session_info(session_id)
        
        assert session_info is not None
        assert session_info['session_id'] == session_id
        assert session_info['query_count'] == 5
        assert 'created_at' in session_info
        assert 'last_accessed' in session_info
        assert session_info['age_minutes'] >= 0
    
    @pytest.mark.asyncio
    async def test_intent_insights_available(self, full_controller):
        """Test intent insights can be retrieved for session."""
        session_id = "insights_test_session"
        
        # Run conversation
        queries = ["running shoes", "marathon training", "best value under $150"]
        for query in queries:
            request = RetrievalRequest(
                query=query,
                context=UserContext(age=30, gender="male"),
                session_id=session_id
            )
            await full_controller.retrieve(request)
        
        # Get intent insights
        insights = await full_controller.intent_evolution_service.get_intent_insights(session_id)
        
        # Verify insights structure
        assert insights['session_id'] == session_id
        assert 'current_stage' in insights
        assert 'next_stage' in insights
        assert 'readiness_score' in insights
        assert 'recommended_strategy' in insights
        assert 0.0 <= insights['readiness_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, full_controller):
        """Test system handles concurrent sessions correctly."""
        # Create 5 concurrent sessions
        sessions = [f"concurrent_session_{i}" for i in range(5)]
        
        async def run_session(session_id):
            for i in range(3):
                request = RetrievalRequest(
                    query=f"query {i} for {session_id}",
                    context=UserContext(age=30, gender="male"),
                    session_id=session_id
                )
                await full_controller.retrieve(request)
        
        # Run all sessions concurrently
        await asyncio.gather(*[run_session(sid) for sid in sessions])
        
        # Verify all sessions tracked correctly
        for session_id in sessions:
            queries = full_controller.session_state_repo.get_session_queries(session_id)
            assert len(queries) == 3
    
    @pytest.mark.asyncio
    async def test_error_in_graphiti_doesnt_break_flow(self, mock_services):
        """Test Graphiti errors don't break the conversation flow."""
        session_state_repo = SessionStateRepository(ttl_minutes=30)
        
        # Create Graphiti that always fails
        mock_graphiti_repo = Mock()
        mock_graphiti_repo.is_initialized = True
        mock_graphiti_repo.add_episode = AsyncMock(side_effect=Exception("Neo4j error"))
        
        graphiti_service = GraphitiService(mock_graphiti_repo)
        intent_evolution_service = IntentEvolutionService(mock_graphiti_repo)
        ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            graphiti_service=graphiti_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
        
        # Should still work despite Graphiti errors
        request = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id="error_test_session"
        )
        
        response = await controller.retrieve(request)
        
        # Should succeed despite Graphiti failure
        assert response.ad_eligibility > 0.0
        assert len(response.campaigns) > 0
        assert response.latency_ms < 100
    
    @pytest.mark.asyncio
    async def test_long_conversation(self, full_controller):
        """Test system handles long conversations (10+ queries)."""
        session_id = "long_conversation_test"
        
        # Run 15 queries
        for i in range(15):
            request = RetrievalRequest(
                query=f"running shoes query number {i}",
                context=UserContext(age=30, gender="male"),
                session_id=session_id
            )
            
            response = await full_controller.retrieve(request)
            
            assert response.ad_eligibility > 0.0
            assert len(response.campaigns) > 0
            assert response.latency_ms < 100
        
        # Verify all queries tracked
        queries = full_controller.session_state_repo.get_session_queries(session_id)
        assert len(queries) == 15
        
        # Verify session info
        session_info = full_controller.session_state_repo.get_session_info(session_id)
        assert session_info['query_count'] == 15

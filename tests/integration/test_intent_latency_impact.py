"""Critical latency tests for intent evolution feature."""

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from statistics import mean, stdev
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


class TestIntentEvolutionLatency:
    """Critical latency tests to ensure P95 < 100ms."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mocked services for latency testing."""
        # Mock all services with fast responses
        eligibility_service = Mock(spec=EligibilityService)
        eligibility_service.score = AsyncMock(return_value=(0.8, None))
        
        category_service = Mock(spec=CategoryService)
        category_service.extract = AsyncMock(return_value=['running_shoes'])
        
        embedding_service = Mock(spec=EmbeddingService)
        embedding_service.embed_query = AsyncMock(return_value=[0.1] * 384)
        
        search_service = Mock(spec=SearchService)
        search_service.search = AsyncMock(return_value=[
            {
                'campaign_id': f'c{i}',
                'title': f'Campaign {i}',
                'category': 'running_shoes',
                'similarity_score': 0.9 - (i * 0.001),
                'description': 'Test campaign',
                'keywords': ['running', 'shoes']
            }
            for i in range(100)
        ])
        
        return {
            'eligibility': eligibility_service,
            'category': category_service,
            'embedding': embedding_service,
            'search': search_service
        }
    
    @pytest.fixture
    def session_state_repo(self):
        """Create real SessionStateRepository."""
        return SessionStateRepository(ttl_minutes=30)
    
    @pytest.fixture
    def mock_graphiti_repo(self):
        """Create mock Graphiti repository."""
        repo = Mock()
        repo.is_initialized = True
        repo.add_episode = AsyncMock()
        return repo
    
    @pytest.fixture
    def intent_evolution_service(self, mock_graphiti_repo):
        """Create IntentEvolutionService with mocked repository."""
        return IntentEvolutionService(mock_graphiti_repo)
    
    @pytest.mark.asyncio
    async def test_baseline_latency_without_intent(self, mock_services):
        """Measure baseline latency without intent evolution."""
        ranking_service = RankingService()  # No intent service
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service
        )
        
        request = RetrievalRequest(
            query="running shoes for marathon",
            context=UserContext(age=30, gender="male")
        )
        
        # Measure latency over 10 requests
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            response = await controller.retrieve(request)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
        
        avg_latency = mean(latencies)
        max_latency = max(latencies)
        
        print(f"\nBaseline (no intent): avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")
        
        # Baseline should be well under 100ms with mocked services
        assert avg_latency < 50, f"Baseline too slow: {avg_latency:.2f}ms"
        assert max_latency < 100, f"Baseline P100 too slow: {max_latency:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_latency_with_intent_tracking(self, mock_services, session_state_repo, intent_evolution_service):
        """Measure latency with intent evolution enabled."""
        ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
        
        request = RetrievalRequest(
            query="running shoes for marathon",
            context=UserContext(age=30, gender="male"),
            session_id="test_session_123"
        )
        
        # Measure latency over 10 requests
        latencies = []
        for i in range(10):
            start = time.perf_counter()
            response = await controller.retrieve(request)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
            
            # Vary query slightly
            request.query = f"running shoes for marathon {i}"
        
        avg_latency = mean(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"\nWith intent: avg={avg_latency:.2f}ms, p95={p95_latency:.2f}ms, max={max_latency:.2f}ms")
        
        # CRITICAL: P95 must be under 100ms
        assert p95_latency < 100, f"P95 latency too high: {p95_latency:.2f}ms"
        assert avg_latency < 75, f"Average latency too high: {avg_latency:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_latency_difference_is_minimal(self, mock_services, session_state_repo, intent_evolution_service):
        """Test that intent evolution adds minimal overhead."""
        # Without intent
        ranking_no_intent = RankingService()
        controller_no_intent = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_no_intent
        )
        
        # With intent
        ranking_with_intent = RankingService(intent_evolution_service=intent_evolution_service)
        controller_with_intent = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_with_intent,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
        
        request_no_intent = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male")
        )
        
        request_with_intent = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id="test_session"
        )
        
        # Measure without intent
        latencies_no_intent = []
        for _ in range(20):
            start = time.perf_counter()
            await controller_no_intent.retrieve(request_no_intent)
            latencies_no_intent.append((time.perf_counter() - start) * 1000)
        
        # Measure with intent
        latencies_with_intent = []
        for _ in range(20):
            start = time.perf_counter()
            await controller_with_intent.retrieve(request_with_intent)
            latencies_with_intent.append((time.perf_counter() - start) * 1000)
        
        avg_no_intent = mean(latencies_no_intent)
        avg_with_intent = mean(latencies_with_intent)
        overhead = avg_with_intent - avg_no_intent
        
        print(f"\nOverhead: {overhead:.2f}ms ({(overhead/avg_no_intent)*100:.1f}%)")
        
        # Intent evolution should add < 10ms overhead
        assert overhead < 10, f"Intent overhead too high: {overhead:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_session_lookup_performance(self, session_state_repo):
        """Test session state lookup is fast (< 1ms)."""
        session_id = "perf_test_session"
        
        # Add some queries
        for i in range(10):
            session_state_repo.add_query(session_id, {
                'query': f'query {i}',
                'timestamp': datetime.now(),
                'eligibility': 0.8
            })
        
        # Measure lookup time
        lookup_times = []
        for _ in range(100):
            start = time.perf_counter()
            queries = session_state_repo.get_session_queries(session_id)
            lookup_time_ms = (time.perf_counter() - start) * 1000
            lookup_times.append(lookup_time_ms)
        
        avg_lookup = mean(lookup_times)
        max_lookup = max(lookup_times)
        
        print(f"\nSession lookup: avg={avg_lookup:.3f}ms, max={max_lookup:.3f}ms")
        
        # Session lookup should be < 1ms
        assert avg_lookup < 1.0, f"Session lookup too slow: {avg_lookup:.3f}ms"
        assert max_lookup < 2.0, f"Max session lookup too slow: {max_lookup:.3f}ms"
    
    @pytest.mark.asyncio
    async def test_intent_query_is_async(self, mock_services, session_state_repo, mock_graphiti_repo):
        """Verify intent queries don't block if used in ranking."""
        # Create slow intent service (simulates slow Neo4j query)
        slow_intent_service = IntentEvolutionService(mock_graphiti_repo)
        
        # Mock slow trajectory query (200ms)
        async def slow_trajectory(session_id):
            await asyncio.sleep(0.2)  # 200ms delay
            return {
                'current_stage': 'AWARENESS',
                'velocity': 0.0,
                'signals': {},
                'query_count': 1
            }
        
        slow_intent_service.get_session_intent_trajectory = slow_trajectory
        
        ranking_service = RankingService(intent_evolution_service=slow_intent_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=slow_intent_service
        )
        
        request = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id="slow_test"
        )
        
        # Measure latency
        start = time.perf_counter()
        response = await controller.retrieve(request)
        latency_ms = (time.perf_counter() - start) * 1000
        
        print(f"\nWith slow intent service: {latency_ms:.2f}ms")
        
        # Even with slow intent service, should still be under 300ms
        # (Intent query happens during ranking, but is cached)
        assert latency_ms < 300, f"Too slow even with caching: {latency_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_graphiti_recording_is_non_blocking(self, mock_services, session_state_repo, mock_graphiti_repo):
        """Test Graphiti recording doesn't block response."""
        # Create slow Graphiti recording (simulates slow Neo4j write)
        async def slow_add_episode(*args, **kwargs):
            await asyncio.sleep(0.5)  # 500ms delay
        
        mock_graphiti_repo.add_episode = slow_add_episode
        
        graphiti_service = GraphitiService(mock_graphiti_repo)
        intent_service = IntentEvolutionService(mock_graphiti_repo)
        ranking_service = RankingService(intent_evolution_service=intent_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            graphiti_service=graphiti_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_service
        )
        
        request = RetrievalRequest(
            query="running shoes",
            context=UserContext(age=30, gender="male"),
            session_id="async_test"
        )
        
        # Measure response latency
        start = time.perf_counter()
        response = await controller.retrieve(request)
        latency_ms = (time.perf_counter() - start) * 1000
        
        print(f"\nWith slow Graphiti (500ms): response={latency_ms:.2f}ms")
        
        # Response should be fast despite slow Graphiti (fire-and-forget)
        assert latency_ms < 100, f"Graphiti blocking response: {latency_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests_with_intent(self, mock_services, session_state_repo, intent_evolution_service):
        """Test system handles concurrent requests with intent tracking."""
        ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
        
        # Create 10 concurrent requests with different sessions
        requests = [
            RetrievalRequest(
                query=f"running shoes {i}",
                context=UserContext(age=30, gender="male"),
                session_id=f"concurrent_session_{i}"
            )
            for i in range(10)
        ]
        
        # Execute concurrently
        start = time.perf_counter()
        tasks = [controller.retrieve(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        total_time_ms = (time.perf_counter() - start) * 1000
        
        # All requests should complete
        assert len(responses) == 10
        
        # Total time should be reasonable (concurrent execution)
        print(f"\n10 concurrent requests: {total_time_ms:.2f}ms total")
        
        # With concurrency, should be much faster than 10 * 100ms
        assert total_time_ms < 500, f"Concurrent requests too slow: {total_time_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_p95_latency_with_100_requests(self, mock_services, session_state_repo, intent_evolution_service):
        """Critical test: P95 latency under 100ms over 100 requests."""
        ranking_service = RankingService(intent_evolution_service=intent_evolution_service)
        
        controller = RetrievalController(
            eligibility_service=mock_services['eligibility'],
            category_service=mock_services['category'],
            embedding_service=mock_services['embedding'],
            search_service=mock_services['search'],
            ranking_service=ranking_service,
            session_state_repo=session_state_repo,
            intent_evolution_service=intent_evolution_service
        )
        
        # Run 100 requests
        latencies = []
        for i in range(100):
            request = RetrievalRequest(
                query=f"running shoes query {i}",
                context=UserContext(age=30, gender="male"),
                session_id=f"session_{i % 10}"  # 10 different sessions
            )
            
            start = time.perf_counter()
            response = await controller.retrieve(request)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
        
        # Calculate statistics
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[49]
        p95 = latencies_sorted[94]
        p99 = latencies_sorted[98]
        avg = mean(latencies)
        std = stdev(latencies)
        
        print(f"\n100 requests statistics:")
        print(f"  Avg: {avg:.2f}ms")
        print(f"  Std: {std:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # CRITICAL: P95 must be under 100ms
        assert p95 < 100, f"P95 latency requirement violated: {p95:.2f}ms"
        assert p99 < 150, f"P99 latency too high: {p99:.2f}ms"
        assert avg < 75, f"Average latency too high: {avg:.2f}ms"

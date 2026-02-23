"""
Integration tests for Phase 3: Eligibility Service

Tests the integration between BlocklistRepository and EligibilityService
with real data files.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.repositories.blocklist_repository import BlocklistRepository
from src.services.eligibility_service import EligibilityService


class TestPhase3Integration:
    """Integration tests for Phase 3 components"""
    
    @pytest.fixture
    def eligibility_service(self):
        """Create an EligibilityService with real blocklist"""
        project_root = Path(__file__).parent.parent.parent
        blocklist_path = project_root / "data" / "blocklist.txt"
        blocklist_repo = BlocklistRepository(str(blocklist_path))
        return EligibilityService(blocklist_repo)
    
    @pytest.mark.asyncio
    async def test_end_to_end_commercial_query(self, eligibility_service):
        """Test complete flow for commercial query"""
        query = "Best running shoes for marathon training"
        context = {
            "age": 25,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness", "running"]
        }
        
        score, _ = await eligibility_service.score(query, context)
        
        # Should have high eligibility for commercial query
        assert 0.8 <= score <= 1.0
        assert score == 0.95  # Exact expected score for commercial intent
    
    @pytest.mark.asyncio
    async def test_end_to_end_blocked_query(self, eligibility_service):
        """Test complete flow for blocked query"""
        query = "I want to commit suicide"
        
        score, _ = await eligibility_service.score(query)
        
        # Should be blocked
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_end_to_end_sensitive_query(self, eligibility_service):
        """Test complete flow for sensitive query"""
        query = "I just got fired from my job and need help"
        
        score, _ = await eligibility_service.score(query)
        
        # Should have low eligibility for sensitive content
        assert 0.3 <= score <= 0.5
    
    @pytest.mark.asyncio
    async def test_end_to_end_informational_query(self, eligibility_service):
        """Test complete flow for informational query"""
        query = "What is the history of the marathon?"
        
        score, _ = await eligibility_service.score(query)
        
        # Should have medium eligibility for informational content
        assert 0.7 <= score <= 0.85
    
    @pytest.mark.asyncio
    async def test_multiple_queries_batch(self, eligibility_service):
        """Test processing multiple queries in sequence"""
        queries = [
            ("buy running shoes", 0.95),
            ("suicide help", 0.0),
            "I'm depressed",
            "how to train for 5k",
        ]
        
        for query_data in queries:
            if isinstance(query_data, tuple):
                query, expected_score = query_data
                score, _ = await eligibility_service.score(query)
                assert score == expected_score, f"Query '{query}' got {score}, expected {expected_score}"
            else:
                query = query_data
                score, _ = await eligibility_service.score(query)
                assert 0.0 <= score <= 1.0, f"Query '{query}' got invalid score {score}"
    
    @pytest.mark.asyncio
    async def test_latency_performance(self, eligibility_service):
        """Test that eligibility scoring is fast"""
        import time
        
        query = "Best running shoes for marathon"
        
        # Warm-up
        await eligibility_service.score(query)
        
        # Measure 100 calls
        start = time.perf_counter()
        for _ in range(100):
            await eligibility_service.score(query)
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 100) * 1000
        
        # Should be well under 10ms per call
        assert avg_latency_ms < 10, f"Average latency {avg_latency_ms:.2f}ms exceeds 10ms target"
        print(f"\n✅ Average eligibility scoring latency: {avg_latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_context_variations(self, eligibility_service):
        """Test that context parameter doesn't break scoring"""
        query = "buy running shoes"
        
        contexts = [
            None,
            {},
            {"age": 25},
            {"age": 25, "gender": "male"},
            {"age": 25, "gender": "male", "location": "SF", "interests": ["fitness"]},
        ]
        
        for context in contexts:
            score, _ = await eligibility_service.score(query, context)
            assert score == 0.95, f"Context {context} changed score to {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

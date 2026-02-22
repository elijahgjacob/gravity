"""
Unit tests for Phase 3: Eligibility Service

Tests the BlocklistRepository and EligibilityService components
to ensure proper ad eligibility scoring.
"""

import pytest
import tempfile
import os
from src.repositories.blocklist_repository import BlocklistRepository
from src.services.eligibility_service import EligibilityService


class TestBlocklistRepository:
    """Test suite for BlocklistRepository"""
    
    @pytest.fixture
    def temp_blocklist(self):
        """Create a temporary blocklist file for testing"""
        content = """# Test blocklist
suicide
kill myself
self harm
how to die

# Explicit content
porn
xxx
nsfw

# Hate speech
hate term 1
hate term 2

# Illegal activities
make bomb
buy drugs
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_load_blocklist(self, temp_blocklist):
        """Test that blocklist loads correctly"""
        repo = BlocklistRepository(temp_blocklist)
        
        # Should have loaded non-comment, non-empty lines
        assert repo.get_blocked_terms_count() > 0
        assert "suicide" in repo.blocked_terms
        assert "porn" in repo.blocked_terms
        assert "make bomb" in repo.blocked_terms
    
    def test_contains_blocked_content_exact_match(self, temp_blocklist):
        """Test exact match detection"""
        repo = BlocklistRepository(temp_blocklist)
        
        # Should detect exact matches
        assert repo.contains_blocked_content("I want to commit suicide")
        assert repo.contains_blocked_content("how to make bomb")
        assert repo.contains_blocked_content("where to buy drugs")
    
    def test_contains_blocked_content_case_insensitive(self, temp_blocklist):
        """Test case-insensitive matching"""
        repo = BlocklistRepository(temp_blocklist)
        
        # Should match regardless of case
        assert repo.contains_blocked_content("SUICIDE help")
        assert repo.contains_blocked_content("Porn videos")
        assert repo.contains_blocked_content("NSFW content")
    
    def test_contains_blocked_content_word_boundaries(self, temp_blocklist):
        """Test word boundary matching"""
        repo = BlocklistRepository(temp_blocklist)
        
        # Should match with word boundaries
        assert repo.contains_blocked_content("I want to kill myself")
        assert repo.contains_blocked_content("self harm resources")
    
    def test_does_not_contain_blocked_content(self, temp_blocklist):
        """Test that safe queries are not blocked"""
        repo = BlocklistRepository(temp_blocklist)
        
        # Should not match safe queries
        assert not repo.contains_blocked_content("running shoes for marathon")
        assert not repo.contains_blocked_content("best laptop for programming")
        assert not repo.contains_blocked_content("how to make a cake")


class TestEligibilityService:
    """Test suite for EligibilityService"""
    
    @pytest.fixture
    def eligibility_service(self, temp_blocklist):
        """Create an EligibilityService instance for testing"""
        blocklist_repo = BlocklistRepository(temp_blocklist)
        return EligibilityService(blocklist_repo)
    
    @pytest.fixture
    def temp_blocklist(self):
        """Create a temporary blocklist file for testing"""
        content = """suicide
kill myself
self harm
porn
xxx
nsfw
make bomb
buy drugs
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_blocklist_queries_return_zero(self, eligibility_service):
        """Test that blocklisted queries return 0.0"""
        # Self-harm queries
        score = await eligibility_service.score("I want to commit suicide")
        assert score == 0.0
        
        score = await eligibility_service.score("how to kill myself")
        assert score == 0.0
        
        # Explicit content
        score = await eligibility_service.score("porn videos")
        assert score == 0.0
        
        # Illegal activities
        score = await eligibility_service.score("how to make bomb")
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_sensitive_queries_return_low_score(self, eligibility_service):
        """Test that sensitive queries return 0.3-0.5"""
        test_cases = [
            ("I just got fired from my job", "Financial distress - fired"),
            ("I'm feeling really depressed", "Mental health - depressed"),
            ("having a panic attack", "Mental health - panic attack"),
        ]
        
        for query, description in test_cases:
            score = await eligibility_service.score(query)
            assert 0.3 <= score <= 0.5, f"{description}: '{query}' got score {score}, expected 0.3-0.5"
    
    @pytest.mark.asyncio
    async def test_commercial_queries_return_high_score(self, eligibility_service):
        """Test that commercial intent queries return 0.8-1.0"""
        # Purchase intent
        score = await eligibility_service.score("buy running shoes")
        assert 0.8 <= score <= 1.0
        
        score = await eligibility_service.score("where to purchase laptop")
        assert 0.8 <= score <= 1.0
        
        # Research intent
        score = await eligibility_service.score("best running shoes for flat feet")
        assert 0.8 <= score <= 1.0
        
        score = await eligibility_service.score("compare iPhone vs Android")
        assert 0.8 <= score <= 1.0
        
        # Price intent
        score = await eligibility_service.score("cheap flights to Paris")
        assert 0.8 <= score <= 1.0
        
        score = await eligibility_service.score("how much does a MacBook cost")
        assert 0.8 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_informational_queries_return_medium_score(self, eligibility_service):
        """Test that informational queries return 0.7-0.85"""
        # General questions
        score = await eligibility_service.score("What is the history of the marathon?")
        assert 0.7 <= score <= 0.85
        
        score = await eligibility_service.score("How do I train for a 5k?")
        assert 0.7 <= score <= 0.85
        
        score = await eligibility_service.score("Why do runners get blisters?")
        assert 0.7 <= score <= 0.85
    
    @pytest.mark.asyncio
    async def test_edge_cases(self, eligibility_service):
        """Test edge cases and boundary conditions"""
        # Empty query
        score = await eligibility_service.score("")
        assert 0.0 <= score <= 1.0
        
        # Very long query
        long_query = "running shoes " * 100
        score = await eligibility_service.score(long_query)
        assert 0.0 <= score <= 1.0
        
        # Special characters
        score = await eligibility_service.score("What's the best running shoe?!?")
        assert 0.8 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_context_parameter(self, eligibility_service):
        """Test that context parameter is accepted"""
        context = {
            "age": 25,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness", "running"]
        }
        
        score = await eligibility_service.score("best running shoes", context)
        assert 0.8 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_score_consistency(self, eligibility_service):
        """Test that same query returns same score"""
        query = "buy running shoes"
        
        score1 = await eligibility_service.score(query)
        score2 = await eligibility_service.score(query)
        score3 = await eligibility_service.score(query)
        
        assert score1 == score2 == score3


class TestEligibilityServiceRealWorldQueries:
    """Test suite with real-world query examples"""
    
    @pytest.fixture
    def eligibility_service(self):
        """Create an EligibilityService with actual blocklist"""
        blocklist_repo = BlocklistRepository("data/blocklist.txt")
        return EligibilityService(blocklist_repo)
    
    @pytest.mark.asyncio
    async def test_high_eligibility_queries(self, eligibility_service):
        """Test queries that should have high eligibility (0.8-1.0)"""
        high_eligibility_queries = [
            "Best running shoes for flat feet",
            "Where to buy iPhone 15",
            "Compare Honda vs Toyota reliability",
            "Cheap flights to New York",
            "Top rated coffee makers",
            "How much does a Tesla cost",
            "Affordable gym memberships near me",
            "Review of Nike Air Zoom Pegasus"
        ]
        
        for query in high_eligibility_queries:
            score = await eligibility_service.score(query)
            assert score >= 0.8, f"Query '{query}' should have high eligibility, got {score}"
    
    @pytest.mark.asyncio
    async def test_medium_eligibility_queries(self, eligibility_service):
        """Test queries that should have medium eligibility (0.7-0.85)"""
        medium_eligibility_queries = [
            "What is the history of the marathon?",
            "How do I train for a 5k?",
            "Why do runners get blisters?",
            "What causes muscle soreness after running?",
            "How to tie running shoes properly"
        ]
        
        for query in medium_eligibility_queries:
            score = await eligibility_service.score(query)
            assert 0.7 <= score <= 0.85, f"Query '{query}' should have medium eligibility, got {score}"
    
    @pytest.mark.asyncio
    async def test_low_eligibility_queries(self, eligibility_service):
        """Test queries that should have low eligibility (0.3-0.5)"""
        low_eligibility_queries = [
            "I just got fired from my job",
            "My mom passed away last year",
            "I'm feeling really depressed",
            "Unemployment benefits application",
            "Can't pay my bills this month"
        ]
        
        for query in low_eligibility_queries:
            score = await eligibility_service.score(query)
            assert 0.3 <= score <= 0.5, f"Query '{query}' should have low eligibility, got {score}"
    
    @pytest.mark.asyncio
    async def test_zero_eligibility_queries(self, eligibility_service):
        """Test queries that should have zero eligibility (0.0)"""
        zero_eligibility_queries = [
            "I want to kill myself",
            "how to commit suicide",
            "self harm methods"
        ]
        
        for query in zero_eligibility_queries:
            score = await eligibility_service.score(query)
            assert score == 0.0, f"Query '{query}' should have zero eligibility, got {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration tests for Phase 6: Ranking System.

Tests the RankingService with various ranking scenarios including
category matching, context-based targeting, and relevance scoring.
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.ranking_service import RankingService


class TestPhase6Integration:
    """Integration tests for Phase 6 ranking service."""
    
    @pytest.fixture
    def ranking_service(self):
        """Create ranking service fixture."""
        return RankingService()
    
    @pytest.fixture
    def sample_campaigns(self):
        """Create sample campaigns for testing."""
        return [
            {
                'campaign_id': 'camp_001',
                'title': 'Premium Running Shoes',
                'description': 'Best running shoes for marathon training',
                'category': 'running_shoes',
                'subcategories': ['athletic_footwear', 'marathon_gear'],
                'similarity_score': 0.85,
                'targeting': {
                    'age_min': 18,
                    'age_max': 45,
                    'genders': ['male', 'female'],
                    'locations': ['CA', 'NY', 'TX'],
                    'interests': ['fitness', 'running', 'health']
                }
            },
            {
                'campaign_id': 'camp_002',
                'title': 'Budget Running Shoes',
                'description': 'Affordable running shoes',
                'category': 'running_shoes',
                'subcategories': ['athletic_footwear'],
                'similarity_score': 0.75,
                'targeting': {
                    'age_min': 18,
                    'age_max': 65,
                    'genders': ['male', 'female'],
                    'locations': ['CA', 'FL'],
                    'interests': ['fitness', 'running']
                }
            },
            {
                'campaign_id': 'camp_003',
                'title': 'Laptop Computer',
                'description': 'High-performance laptop',
                'category': 'laptops',
                'subcategories': ['electronics', 'computers'],
                'similarity_score': 0.45,
                'targeting': {
                    'age_min': 20,
                    'age_max': 50,
                    'genders': ['male', 'female'],
                    'locations': ['CA', 'WA'],
                    'interests': ['technology', 'programming']
                }
            },
            {
                'campaign_id': 'camp_004',
                'title': 'Yoga Mat',
                'description': 'Premium yoga mat',
                'category': 'yoga_equipment',
                'subcategories': ['fitness_equipment'],
                'similarity_score': 0.60,
                'targeting': {
                    'age_min': 25,
                    'age_max': 55,
                    'genders': ['female'],
                    'locations': ['CA', 'NY'],
                    'interests': ['fitness', 'yoga', 'wellness']
                }
            },
            {
                'campaign_id': 'camp_005',
                'title': 'Marathon Training Program',
                'description': 'Complete marathon training',
                'category': 'marathon_gear',
                'subcategories': ['training', 'fitness'],
                'similarity_score': 0.80,
                'targeting': {
                    'age_min': 20,
                    'age_max': 50,
                    'genders': ['male', 'female'],
                    'locations': ['CA', 'NY', 'MA'],
                    'interests': ['running', 'marathon', 'fitness']
                }
            }
        ]
    
    # ========== Basic Ranking Tests ==========
    
    @pytest.mark.asyncio
    async def test_basic_ranking_without_context(self, ranking_service, sample_campaigns):
        """Test basic ranking without user context."""
        query = "running shoes"
        categories = ["running_shoes"]
        
        ranked = await ranking_service.rank(
            campaigns=sample_campaigns.copy(),
            query=query,
            categories=categories,
            context=None
        )
        
        # Verify all campaigns have relevance_score
        assert all('relevance_score' in c for c in ranked)
        
        # Verify sorted by relevance (descending)
        for i in range(len(ranked) - 1):
            assert ranked[i]['relevance_score'] >= ranked[i + 1]['relevance_score']
        
        # Top result should be running shoes with category match
        assert ranked[0]['category'] == 'running_shoes'
    
    @pytest.mark.asyncio
    async def test_ranking_with_context(self, ranking_service, sample_campaigns):
        """Test ranking with user context."""
        query = "running shoes"
        categories = ["running_shoes"]
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'San Francisco, CA',
            'interests': ['fitness', 'running', 'health']
        }
        
        ranked = await ranking_service.rank(
            campaigns=sample_campaigns.copy(),
            query=query,
            categories=categories,
            context=context
        )
        
        # All campaigns should have relevance scores
        assert all('relevance_score' in c for c in ranked)
        
        # Verify sorted by relevance
        for i in range(len(ranked) - 1):
            assert ranked[i]['relevance_score'] >= ranked[i + 1]['relevance_score']
    
    @pytest.mark.asyncio
    async def test_category_boost_exact_match(self, ranking_service):
        """Test that exact category matches get boosted."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'running_shoes',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {}
            },
            {
                'campaign_id': 'camp_2',
                'category': 'laptops',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {}
            }
        ]
        
        categories = ["running_shoes"]
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="shoes",
            categories=categories,
            context=None
        )
        
        # Campaign with matching category should be ranked higher
        assert ranked[0]['campaign_id'] == 'camp_1'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
        
        # Exact match should get 1.3x boost
        expected_score = min(0.70 * 1.3, 1.0)
        assert abs(ranked[0]['relevance_score'] - expected_score) < 0.01
    
    @pytest.mark.asyncio
    async def test_category_boost_subcategory_match(self, ranking_service):
        """Test that subcategory matches get boosted."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'shoes',
                'subcategories': ['running_shoes', 'athletic_footwear'],
                'similarity_score': 0.70,
                'targeting': {}
            },
            {
                'campaign_id': 'camp_2',
                'category': 'shoes',
                'subcategories': ['casual_shoes'],
                'similarity_score': 0.70,
                'targeting': {}
            }
        ]
        
        categories = ["running_shoes"]
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="running shoes",
            categories=categories,
            context=None
        )
        
        # Campaign with matching subcategory should be ranked higher
        assert ranked[0]['campaign_id'] == 'camp_1'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
    
    @pytest.mark.asyncio
    async def test_category_boost_both_exact_and_subcategory(self, ranking_service):
        """Test combined exact and subcategory boosts."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'running_shoes',
                'subcategories': ['athletic_footwear'],
                'similarity_score': 0.70,
                'targeting': {}
            }
        ]
        
        categories = ["running_shoes", "athletic_footwear"]
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="running shoes",
            categories=categories,
            context=None
        )
        
        # Should get both boosts: 0.70 * 1.3 * 1.15 = 1.0465 -> capped at 1.0
        assert ranked[0]['relevance_score'] == 1.0
    
    # ========== Context-Based Targeting Tests ==========
    
    @pytest.mark.asyncio
    async def test_age_targeting_boost(self, ranking_service):
        """Test age targeting boost."""
        campaigns = [
            {
                'campaign_id': 'camp_young',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'age_min': 18,
                    'age_max': 30
                }
            },
            {
                'campaign_id': 'camp_old',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'age_min': 50,
                    'age_max': 70
                }
            }
        ]
        
        context = {'age': 25}
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        # Young campaign should be boosted
        assert ranked[0]['campaign_id'] == 'camp_young'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
    
    @pytest.mark.asyncio
    async def test_gender_targeting_boost(self, ranking_service):
        """Test gender targeting boost."""
        campaigns = [
            {
                'campaign_id': 'camp_male',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'genders': ['male']
                }
            },
            {
                'campaign_id': 'camp_female',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'genders': ['female']
                }
            }
        ]
        
        context = {'gender': 'male'}
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        # Male-targeted campaign should be boosted
        assert ranked[0]['campaign_id'] == 'camp_male'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
    
    @pytest.mark.asyncio
    async def test_location_targeting_boost(self, ranking_service):
        """Test location targeting boost."""
        campaigns = [
            {
                'campaign_id': 'camp_ca',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'locations': ['CA', 'San Francisco']
                }
            },
            {
                'campaign_id': 'camp_ny',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'locations': ['NY', 'New York']
                }
            }
        ]
        
        context = {'location': 'San Francisco, CA'}
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        # CA campaign should be boosted
        assert ranked[0]['campaign_id'] == 'camp_ca'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
    
    @pytest.mark.asyncio
    async def test_interest_targeting_boost(self, ranking_service):
        """Test interest alignment boost."""
        campaigns = [
            {
                'campaign_id': 'camp_fitness',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'interests': ['fitness', 'running', 'health']
                }
            },
            {
                'campaign_id': 'camp_tech',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'interests': ['technology', 'gaming']
                }
            }
        ]
        
        context = {'interests': ['fitness', 'running', 'health']}
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        # Fitness campaign should be boosted (3 overlapping interests)
        assert ranked[0]['campaign_id'] == 'camp_fitness'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
        
        # Should get 1.0 + (0.1 * 3) = 1.3x boost
        # 0.70 * 1.3 = 0.91, but may be capped at 1.0
        assert ranked[0]['relevance_score'] >= 0.91
    
    @pytest.mark.asyncio
    async def test_multiple_context_boosts(self, ranking_service):
        """Test combined context boosts."""
        campaigns = [
            {
                'campaign_id': 'camp_perfect_match',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'age_min': 25,
                    'age_max': 35,
                    'genders': ['male'],
                    'locations': ['CA'],
                    'interests': ['fitness', 'running']
                }
            },
            {
                'campaign_id': 'camp_no_match',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'age_min': 50,
                    'age_max': 70,
                    'genders': ['female'],
                    'locations': ['NY'],
                    'interests': ['cooking']
                }
            }
        ]
        
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'San Francisco, CA',
            'interests': ['fitness', 'running']
        }
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        # Perfect match should be ranked much higher
        assert ranked[0]['campaign_id'] == 'camp_perfect_match'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']
        
        # Should get multiple boosts: age(1.1) * gender(1.05) * location(1.15) * interests(1.2)
        # 0.70 * 1.1 * 1.05 * 1.15 * 1.2 = 1.14 -> capped at 1.0
        assert ranked[0]['relevance_score'] == 1.0
    
    # ========== Edge Cases and Validation ==========
    
    @pytest.mark.asyncio
    async def test_ranking_empty_campaigns(self, ranking_service):
        """Test ranking with empty campaign list."""
        ranked = await ranking_service.rank(
            campaigns=[],
            query="test",
            categories=["test"],
            context=None
        )
        
        assert ranked == []
    
    @pytest.mark.asyncio
    async def test_ranking_single_campaign(self, ranking_service):
        """Test ranking with single campaign."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.75,
                'targeting': {}
            }
        ]
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=None
        )
        
        assert len(ranked) == 1
        assert 'relevance_score' in ranked[0]
    
    @pytest.mark.asyncio
    async def test_ranking_preserves_campaign_data(self, ranking_service, sample_campaigns):
        """Test that ranking preserves all campaign fields."""
        original_ids = {c['campaign_id'] for c in sample_campaigns}
        
        ranked = await ranking_service.rank(
            campaigns=sample_campaigns.copy(),
            query="test",
            categories=["test"],
            context=None
        )
        
        # All campaigns should be present
        ranked_ids = {c['campaign_id'] for c in ranked}
        assert original_ids == ranked_ids
        
        # All original fields should be preserved
        for campaign in ranked:
            assert 'campaign_id' in campaign
            assert 'title' in campaign
            assert 'description' in campaign
            assert 'category' in campaign
            assert 'similarity_score' in campaign
    
    @pytest.mark.asyncio
    async def test_relevance_score_capped_at_one(self, ranking_service):
        """Test that relevance scores are capped at 1.0."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'running_shoes',
                'subcategories': ['athletic_footwear', 'marathon_gear'],
                'similarity_score': 0.95,
                'targeting': {
                    'age_min': 25,
                    'age_max': 35,
                    'genders': ['male'],
                    'locations': ['CA'],
                    'interests': ['fitness', 'running', 'health']
                }
            }
        ]
        
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'CA',
            'interests': ['fitness', 'running', 'health']
        }
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="running shoes",
            categories=["running_shoes", "athletic_footwear"],
            context=context
        )
        
        # Score should be capped at 1.0
        assert ranked[0]['relevance_score'] <= 1.0
        assert ranked[0]['relevance_score'] == 1.0
    
    @pytest.mark.asyncio
    async def test_ranking_with_missing_targeting_fields(self, ranking_service):
        """Test ranking with campaigns missing targeting fields."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {}  # Empty targeting
            },
            {
                'campaign_id': 'camp_2',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70
                # No targeting field at all
            }
        ]
        
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'CA',
            'interests': ['fitness']
        }
        
        # Should not crash
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context=context
        )
        
        assert len(ranked) == 2
        assert all('relevance_score' in c for c in ranked)
    
    @pytest.mark.asyncio
    async def test_ranking_with_empty_context(self, ranking_service):
        """Test ranking with empty context dictionary."""
        campaigns = [
            {
                'campaign_id': 'camp_1',
                'category': 'product',
                'subcategories': [],
                'similarity_score': 0.70,
                'targeting': {
                    'age_min': 18,
                    'age_max': 65
                }
            }
        ]
        
        ranked = await ranking_service.rank(
            campaigns=campaigns.copy(),
            query="product",
            categories=["product"],
            context={}  # Empty context
        )
        
        assert len(ranked) == 1
        assert 'relevance_score' in ranked[0]
    
    # ========== Performance Tests ==========
    
    @pytest.mark.asyncio
    async def test_ranking_latency_small_batch(self, ranking_service, sample_campaigns):
        """Test ranking latency for small batch."""
        query = "running shoes"
        categories = ["running_shoes"]
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'CA',
            'interests': ['fitness', 'running']
        }
        
        # Warm-up
        await ranking_service.rank(
            campaigns=sample_campaigns.copy(),
            query=query,
            categories=categories,
            context=context
        )
        
        # Measure 100 ranking operations
        start = time.perf_counter()
        for _ in range(100):
            await ranking_service.rank(
                campaigns=sample_campaigns.copy(),
                query=query,
                categories=categories,
                context=context
            )
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 100) * 1000
        
        # Should be very fast for 5 campaigns
        assert avg_latency_ms < 5, f"Average latency {avg_latency_ms:.2f}ms exceeds 5ms target"
        print(f"\n✅ Average ranking latency (5 campaigns): {avg_latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_ranking_latency_large_batch(self, ranking_service):
        """Test ranking latency for large batch (1000 campaigns)."""
        # Create 1000 campaigns
        campaigns = []
        for i in range(1000):
            campaigns.append({
                'campaign_id': f'camp_{i:04d}',
                'title': f'Campaign {i}',
                'category': 'product',
                'subcategories': ['sub1', 'sub2'],
                'similarity_score': 0.5 + (i % 50) / 100,
                'targeting': {
                    'age_min': 18,
                    'age_max': 65,
                    'genders': ['male', 'female'],
                    'locations': ['CA', 'NY'],
                    'interests': ['fitness', 'technology']
                }
            })
        
        query = "product"
        categories = ["product"]
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'CA',
            'interests': ['fitness']
        }
        
        # Warm-up
        await ranking_service.rank(
            campaigns=campaigns.copy(),
            query=query,
            categories=categories,
            context=context
        )
        
        # Measure 10 ranking operations
        start = time.perf_counter()
        for _ in range(10):
            await ranking_service.rank(
                campaigns=campaigns.copy(),
                query=query,
                categories=categories,
                context=context
            )
        elapsed = time.perf_counter() - start
        
        avg_latency_ms = (elapsed / 10) * 1000
        
        # Should be under 20ms for 1000 campaigns
        assert avg_latency_ms < 20, f"Average latency {avg_latency_ms:.2f}ms exceeds 20ms target"
        print(f"\n✅ Average ranking latency (1000 campaigns): {avg_latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_ranking(self, ranking_service, sample_campaigns):
        """Test concurrent ranking operations."""
        queries = [
            ("running shoes", ["running_shoes"]),
            ("laptop computer", ["laptops"]),
            ("yoga mat", ["yoga_equipment"]),
            ("protein powder", ["sports_nutrition"]),
            ("fitness tracker", ["fitness_trackers"]),
        ]
        
        context = {
            'age': 30,
            'gender': 'male',
            'location': 'CA',
            'interests': ['fitness']
        }
        
        # Execute all ranking operations concurrently
        tasks = [
            ranking_service.rank(
                campaigns=sample_campaigns.copy(),
                query=query,
                categories=categories,
                context=context
            )
            for query, categories in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == len(queries)
        for ranked in results:
            assert len(ranked) > 0
            assert all('relevance_score' in c for c in ranked)


def test_phase6_components_exist():
    """Test that all Phase 6 components are properly created."""
    # Check that files exist
    assert Path("src/services/ranking_service.py").exists()
    
    # Check that class can be imported
    from src.services.ranking_service import RankingService
    
    assert RankingService is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

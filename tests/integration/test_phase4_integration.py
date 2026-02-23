"""
Integration tests for Phase 4: Category Extraction System.

Tests the integration between TaxonomyRepository and CategoryService,
verifying end-to-end category extraction functionality.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.category_service import CategoryService
from src.repositories.taxonomy_repository import TaxonomyRepository


class TestPhase4Integration:
    """Integration tests for Phase 4 category extraction."""
    
    @pytest.fixture
    def taxonomy_repo(self):
        """Create taxonomy repository fixture."""
        project_root = Path(__file__).parent.parent.parent
        taxonomy_path = project_root / "data" / "taxonomy.json"
        return TaxonomyRepository(str(taxonomy_path))
    
    @pytest.fixture
    def category_service(self, taxonomy_repo):
        """Create category service fixture."""
        return CategoryService(taxonomy_repo)
    
    @pytest.mark.asyncio
    async def test_basic_category_extraction(self, category_service):
        """Test basic category extraction without context."""
        query = "I need running shoes for my marathon training"
        categories = await category_service.extract(query)
        
        assert len(categories) >= 1
        assert len(categories) <= 10
        assert "running_shoes" in categories or "marathon_gear" in categories
    
    @pytest.mark.asyncio
    async def test_category_extraction_with_context(self, category_service):
        """Test category extraction with user context."""
        query = "best fitness tracker"
        context = {"interests": ["fitness", "health"]}
        categories = await category_service.extract(query, context)
        
        assert len(categories) >= 1
        assert len(categories) <= 10
        assert "fitness_trackers" in categories
    
    @pytest.mark.asyncio
    async def test_commercial_intent_queries(self, category_service):
        """Test queries with strong commercial intent."""
        test_cases = [
            ("buy laptop for programming", ["laptops", "electronics"]),
            ("best smartphone deals", ["smartphones", "electronics"]),
            ("cheap flights to Europe", ["flights", "travel_destinations"]),
            ("compare credit cards", ["credit_cards", "finance"]),
        ]
        
        for query, expected_categories in test_cases:
            categories = await category_service.extract(query)
            assert len(categories) >= 1
            assert len(categories) <= 10
            # At least one expected category should be present
            assert any(exp in categories for exp in expected_categories), \
                f"Query '{query}' did not match expected categories {expected_categories}, got {categories}"
    
    @pytest.mark.asyncio
    async def test_multi_category_queries(self, category_service):
        """Test queries that should match multiple categories."""
        query = "I need running shoes, yoga mat, and protein powder"
        categories = await category_service.extract(query)
        
        assert len(categories) >= 3
        assert len(categories) <= 10
        
        # Should extract multiple relevant categories
        expected = ["running_shoes", "yoga_equipment", "sports_nutrition"]
        matches = sum(1 for exp in expected if exp in categories)
        assert matches >= 2, f"Expected at least 2 matches from {expected}, got {categories}"
    
    @pytest.mark.asyncio
    async def test_context_boosting(self, category_service):
        """Test that context interests boost relevant categories."""
        query = "fitness equipment"
        
        # Without context
        categories_no_context = await category_service.extract(query, context=None)
        
        # With fitness interest context
        context = {"interests": ["fitness", "gym"]}
        categories_with_context = await category_service.extract(query, context)
        
        assert len(categories_no_context) >= 1
        assert len(categories_with_context) >= 1
        
        # Both should have fitness-related categories
        fitness_categories = ["gym_equipment", "athletic_footwear", "fitness_trackers", "athletic_apparel"]
        assert any(cat in categories_no_context for cat in fitness_categories)
        assert any(cat in categories_with_context for cat in fitness_categories)
    
    @pytest.mark.asyncio
    async def test_fallback_to_general(self, category_service):
        """Test fallback to 'general' category for unclear queries."""
        query = "xyz123 random nonsense query"
        categories = await category_service.extract(query)
        
        # Should return at least 1 category (fallback to "general")
        assert len(categories) >= 1
        assert len(categories) <= 10
        # If no matches, should fallback to "general"
        if len(categories) == 1:
            assert "general" in categories
    
    @pytest.mark.asyncio
    async def test_max_categories_constraint(self, category_service):
        """Test that max_categories parameter is respected."""
        query = "fitness health wellness sports running yoga cycling gym training nutrition"
        
        # Test with different max values
        for max_cats in [3, 5, 10]:
            categories = await category_service.extract(query, max_categories=max_cats)
            assert len(categories) <= max_cats
            assert len(categories) >= 1
    
    @pytest.mark.asyncio
    async def test_vertical_specific_queries(self, category_service):
        """Test queries from different verticals."""
        vertical_tests = [
            # Fitness vertical
            ("marathon training gear", ["marathon_gear", "running_shoes"]),
            
            # Technology vertical
            ("gaming laptop with RTX graphics", ["laptops", "gaming", "electronics"]),
            
            # Travel vertical
            ("hotel booking in Paris", ["hotels", "travel_destinations"]),
            
            # Finance vertical
            ("personal loan rates", ["loans", "finance"]),
            
            # Health vertical
            ("vitamins and supplements", ["vitamins_supplements", "health_wellness"]),
            
            # Fashion vertical
            ("designer watches", ["watches", "jewelry", "fashion_clothing"]),
            
            # Home vertical
            ("smart home automation", ["smart_home", "electronics"]),
            
            # Automotive vertical
            ("car insurance quotes", ["insurance", "automotive"]),
        ]
        
        for query, expected_categories in vertical_tests:
            categories = await category_service.extract(query)
            assert len(categories) >= 1
            assert len(categories) <= 10
            
            # At least one expected category should be present
            has_match = any(exp in categories for exp in expected_categories)
            assert has_match, \
                f"Query '{query}' expected {expected_categories}, got {categories}"
    
    @pytest.mark.asyncio
    async def test_keyword_matching_priority(self, category_service):
        """Test that exact keyword matches are prioritized."""
        # Query with exact keyword match
        query = "running shoes for marathon"
        categories = await category_service.extract(query)
        
        # "running_shoes" should be in top results due to exact match
        assert "running_shoes" in categories[:5], \
            f"Expected 'running_shoes' in top 5, got {categories}"
    
    @pytest.mark.asyncio
    async def test_taxonomy_repository_integration(self, taxonomy_repo):
        """Test taxonomy repository functionality."""
        # Test that taxonomy loaded correctly
        assert taxonomy_repo.get_category_count() > 0
        
        # Test get_all_categories
        all_categories = taxonomy_repo.get_all_categories()
        assert len(all_categories) > 0
        assert "running_shoes" in all_categories
        
        # Test get_category
        running_shoes = taxonomy_repo.get_category("running_shoes")
        assert "keywords" in running_shoes
        assert "related" in running_shoes
        assert len(running_shoes["keywords"]) > 0
        
        # Test non-existent category
        non_existent = taxonomy_repo.get_category("nonexistent_category")
        assert non_existent == {}
    
    @pytest.mark.asyncio
    async def test_concurrent_extraction(self, category_service):
        """Test concurrent category extraction requests."""
        queries = [
            "running shoes",
            "laptop for programming",
            "fitness tracker",
            "yoga mat",
            "protein powder",
        ]
        
        # Execute all extractions concurrently
        tasks = [category_service.extract(query) for query in queries]
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == len(queries)
        for categories in results:
            assert len(categories) >= 1
            assert len(categories) <= 10
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, category_service):
        """Test handling of edge cases."""
        # Empty query
        categories = await category_service.extract("")
        assert len(categories) >= 1  # Should fallback to "general"
        
        # Very short query
        categories = await category_service.extract("a")
        assert len(categories) >= 1
        
        # Query with only stopwords
        categories = await category_service.extract("the and or but")
        assert len(categories) >= 1
    
    @pytest.mark.asyncio
    async def test_case_insensitivity(self, category_service):
        """Test that category extraction is case-insensitive."""
        queries = [
            "RUNNING SHOES",
            "running shoes",
            "Running Shoes",
            "RuNnInG sHoEs",
        ]
        
        results = []
        for query in queries:
            categories = await category_service.extract(query)
            results.append(set(categories))
        
        # All should produce similar results (allowing for some variation)
        # At least the top category should be consistent
        first_categories = [list(r)[0] for r in results]
        assert len(set(first_categories)) <= 2, \
            f"Case sensitivity issue: {first_categories}"


def test_phase4_components_exist():
    """Test that all Phase 4 components are properly created."""
    # Check that files exist
    project_root = Path(__file__).parent.parent.parent
    assert (project_root / "src" / "repositories" / "taxonomy_repository.py").exists()
    assert (project_root / "src" / "services" / "category_service.py").exists()
    assert (project_root / "data" / "taxonomy.json").exists()
    
    # Check that classes can be imported
    from src.repositories.taxonomy_repository import TaxonomyRepository
    from src.services.category_service import CategoryService
    
    assert TaxonomyRepository is not None
    assert CategoryService is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

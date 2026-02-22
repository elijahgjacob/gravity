"""
Validation script for Phase 4: Category Extraction System.

This script validates that all Phase 4 components are properly implemented
and functioning correctly.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.category_service import CategoryService
from src.repositories.taxonomy_repository import TaxonomyRepository


class Phase4Validator:
    """Validator for Phase 4 components."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def print_header(self, title: str):
        """Print a section header."""
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    
    def print_test(self, name: str, passed: bool, message: str = ""):
        """Print test result."""
        if passed:
            print(f"✓ {name}")
            self.passed += 1
        else:
            print(f"✗ {name}")
            if message:
                print(f"  └─ {message}")
            self.failed += 1
    
    def print_warning(self, message: str):
        """Print a warning."""
        print(f"⚠ {message}")
        self.warnings += 1
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"  ℹ {message}")
    
    def validate_file_structure(self) -> bool:
        """Validate that all required files exist."""
        self.print_header("FILE STRUCTURE VALIDATION")
        
        required_files = [
            "src/repositories/taxonomy_repository.py",
            "src/services/category_service.py",
            "data/taxonomy.json",
            "tests/test_category_extraction.py",
            "tests/integration/test_phase4_integration.py"
        ]
        
        all_exist = True
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.print_test(f"File exists: {file_path}", exists)
            if not exists:
                all_exist = False
        
        return all_exist
    
    def validate_taxonomy_data(self) -> bool:
        """Validate taxonomy.json structure and content."""
        self.print_header("TAXONOMY DATA VALIDATION")
        
        try:
            with open("data/taxonomy.json", 'r') as f:
                taxonomy = json.load(f)
            
            self.print_test("Taxonomy JSON is valid", True)
            self.print_info(f"Loaded {len(taxonomy)} categories")
            
            # Check minimum number of categories
            min_categories = 40
            has_min = len(taxonomy) >= min_categories
            self.print_test(
                f"Has at least {min_categories} categories", 
                has_min,
                f"Found {len(taxonomy)} categories"
            )
            
            # Validate structure of each category
            valid_structure = True
            categories_checked = 0
            
            for cat_name, cat_data in taxonomy.items():
                if not isinstance(cat_data, dict):
                    self.print_test(
                        f"Category '{cat_name}' has valid structure",
                        False,
                        "Not a dictionary"
                    )
                    valid_structure = False
                    continue
                
                if "keywords" not in cat_data:
                    self.print_test(
                        f"Category '{cat_name}' has keywords",
                        False,
                        "Missing 'keywords' field"
                    )
                    valid_structure = False
                    continue
                
                if "related" not in cat_data:
                    self.print_test(
                        f"Category '{cat_name}' has related terms",
                        False,
                        "Missing 'related' field"
                    )
                    valid_structure = False
                    continue
                
                if not isinstance(cat_data["keywords"], list) or len(cat_data["keywords"]) == 0:
                    self.print_test(
                        f"Category '{cat_name}' has valid keywords",
                        False,
                        "Keywords must be a non-empty list"
                    )
                    valid_structure = False
                    continue
                
                categories_checked += 1
            
            self.print_test(
                f"All {categories_checked} categories have valid structure",
                valid_structure
            )
            
            # Check for expected categories
            expected_categories = [
                "running_shoes", "athletic_footwear", "marathon_gear",
                "fitness_trackers", "laptops", "smartphones", "flights",
                "hotels", "credit_cards", "insurance", "general"
            ]
            
            missing = [cat for cat in expected_categories if cat not in taxonomy]
            has_expected = len(missing) == 0
            
            self.print_test(
                "Has all expected core categories",
                has_expected,
                f"Missing: {missing}" if missing else ""
            )
            
            return has_min and valid_structure and has_expected
            
        except json.JSONDecodeError as e:
            self.print_test("Taxonomy JSON is valid", False, str(e))
            return False
        except Exception as e:
            self.print_test("Taxonomy data validation", False, str(e))
            return False
    
    def validate_taxonomy_repository(self) -> bool:
        """Validate TaxonomyRepository functionality."""
        self.print_header("TAXONOMY REPOSITORY VALIDATION")
        
        try:
            repo = TaxonomyRepository("data/taxonomy.json")
            self.print_test("TaxonomyRepository instantiation", True)
            
            # Test get_category_count
            count = repo.get_category_count()
            self.print_test(
                "get_category_count() returns valid count",
                count > 0,
                f"Count: {count}"
            )
            
            # Test get_all_categories
            all_cats = repo.get_all_categories()
            self.print_test(
                "get_all_categories() returns dictionary",
                isinstance(all_cats, dict) and len(all_cats) > 0,
                f"Returned {len(all_cats)} categories"
            )
            
            # Test get_category with valid category
            running_shoes = repo.get_category("running_shoes")
            self.print_test(
                "get_category() returns valid data for existing category",
                isinstance(running_shoes, dict) and "keywords" in running_shoes,
                f"Keywords: {len(running_shoes.get('keywords', []))}"
            )
            
            # Test get_category with invalid category
            invalid = repo.get_category("nonexistent_category_xyz")
            self.print_test(
                "get_category() returns empty dict for non-existent category",
                invalid == {}
            )
            
            return True
            
        except Exception as e:
            self.print_test("TaxonomyRepository validation", False, str(e))
            return False
    
    async def validate_category_service(self) -> bool:
        """Validate CategoryService functionality."""
        self.print_header("CATEGORY SERVICE VALIDATION")
        
        try:
            repo = TaxonomyRepository("data/taxonomy.json")
            service = CategoryService(repo)
            self.print_test("CategoryService instantiation", True)
            
            # Test basic extraction
            categories = await service.extract("running shoes for marathon")
            self.print_test(
                "extract() returns valid categories",
                isinstance(categories, list) and len(categories) > 0,
                f"Returned {len(categories)} categories: {categories[:3]}"
            )
            
            # Test category count constraint (1-10)
            valid_count = 1 <= len(categories) <= 10
            self.print_test(
                "extract() enforces 1-10 category constraint",
                valid_count,
                f"Returned {len(categories)} categories"
            )
            
            # Test with context
            context = {"interests": ["fitness", "running"]}
            categories_with_context = await service.extract(
                "best fitness tracker",
                context
            )
            self.print_test(
                "extract() works with context",
                isinstance(categories_with_context, list) and len(categories_with_context) > 0,
                f"Returned {len(categories_with_context)} categories"
            )
            
            # Test fallback to "general"
            nonsense = await service.extract("xyz123 random nonsense")
            has_fallback = len(nonsense) >= 1
            self.print_test(
                "extract() provides fallback for unclear queries",
                has_fallback,
                f"Returned: {nonsense}"
            )
            
            # Test max_categories parameter
            limited = await service.extract(
                "fitness health wellness sports running yoga",
                max_categories=3
            )
            self.print_test(
                "extract() respects max_categories parameter",
                len(limited) <= 3,
                f"Requested max 3, got {len(limited)}"
            )
            
            return True
            
        except Exception as e:
            self.print_test("CategoryService validation", False, str(e))
            return False
    
    async def validate_integration_scenarios(self) -> bool:
        """Validate end-to-end integration scenarios."""
        self.print_header("INTEGRATION SCENARIOS")
        
        try:
            repo = TaxonomyRepository("data/taxonomy.json")
            service = CategoryService(repo)
            
            test_scenarios = [
                {
                    "name": "Commercial intent query",
                    "query": "buy laptop for programming",
                    "context": None,
                    "expected_contains": ["laptops", "electronics", "software"]
                },
                {
                    "name": "Multi-category query",
                    "query": "running shoes and yoga mat",
                    "context": None,
                    "expected_contains": ["running_shoes", "yoga_equipment"]
                },
                {
                    "name": "Context-boosted query",
                    "query": "fitness equipment",
                    "context": {"interests": ["fitness", "gym"]},
                    "expected_contains": ["gym_equipment", "athletic_footwear", "fitness_trackers"]
                },
                {
                    "name": "Travel vertical query",
                    "query": "cheap flights to Europe",
                    "context": None,
                    "expected_contains": ["flights", "travel_destinations"]
                },
                {
                    "name": "Finance vertical query",
                    "query": "credit card rewards",
                    "context": None,
                    "expected_contains": ["credit_cards"]
                }
            ]
            
            for scenario in test_scenarios:
                categories = await service.extract(
                    scenario["query"],
                    scenario["context"]
                )
                
                has_match = any(
                    exp in categories 
                    for exp in scenario["expected_contains"]
                )
                
                self.print_test(
                    scenario["name"],
                    has_match,
                    f"Expected one of {scenario['expected_contains']}, got {categories[:3]}"
                )
            
            return True
            
        except Exception as e:
            self.print_test("Integration scenarios", False, str(e))
            return False
    
    async def validate_performance(self) -> bool:
        """Validate performance characteristics."""
        self.print_header("PERFORMANCE VALIDATION")
        
        try:
            import time
            
            repo = TaxonomyRepository("data/taxonomy.json")
            service = CategoryService(repo)
            
            # Warm-up
            await service.extract("test query")
            
            # Test single extraction latency
            query = "running shoes for marathon training"
            start = time.perf_counter()
            categories = await service.extract(query)
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Target: <15ms for category extraction (Phase 4 plan: 5-10ms, allowing buffer)
            target_latency = 15.0
            meets_target = latency_ms < target_latency
            
            self.print_test(
                f"Single extraction latency < {target_latency}ms",
                meets_target,
                f"Actual: {latency_ms:.2f}ms"
            )
            
            if not meets_target:
                self.print_warning(
                    f"Latency {latency_ms:.2f}ms exceeds target {target_latency}ms"
                )
            
            # Test multiple concurrent extractions
            queries = [
                "running shoes",
                "laptop for programming",
                "fitness tracker",
                "yoga mat",
                "protein powder"
            ]
            
            start = time.perf_counter()
            tasks = [service.extract(q) for q in queries]
            results = await asyncio.gather(*tasks)
            total_time = (time.perf_counter() - start) * 1000
            avg_time = total_time / len(queries)
            
            self.print_test(
                f"Concurrent extractions complete",
                len(results) == len(queries),
                f"Avg time: {avg_time:.2f}ms per query"
            )
            
            return True
            
        except Exception as e:
            self.print_test("Performance validation", False, str(e))
            return False
    
    def print_summary(self):
        """Print validation summary."""
        self.print_header("VALIDATION SUMMARY")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ✗")
        print(f"Warnings: {self.warnings} ⚠")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All Phase 4 validations passed!")
            print("✓ TaxonomyRepository is working correctly")
            print("✓ CategoryService is working correctly")
            print("✓ Category extraction meets requirements")
            print("✓ Integration scenarios validated")
            return True
        else:
            print(f"\n❌ {self.failed} validation(s) failed")
            print("Please review the failures above and fix the issues.")
            return False


async def main():
    """Run all Phase 4 validations."""
    validator = Phase4Validator()
    
    print("\n" + "=" * 80)
    print("  PHASE 4 VALIDATION: Category Extraction System")
    print("=" * 80)
    
    # Run all validations
    file_structure_ok = validator.validate_file_structure()
    taxonomy_data_ok = validator.validate_taxonomy_data()
    taxonomy_repo_ok = validator.validate_taxonomy_repository()
    category_service_ok = await validator.validate_category_service()
    integration_ok = await validator.validate_integration_scenarios()
    performance_ok = await validator.validate_performance()
    
    # Print summary
    validator.print_summary()
    
    # Exit with appropriate code
    all_passed = validator.failed == 0
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())

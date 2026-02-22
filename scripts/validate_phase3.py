"""Phase 3 Validation Script - Verify Phase 3 Eligibility Service."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Change to project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def check_phase3_files():
    """Check that all Phase 3 files exist."""
    print("=" * 60)
    print("PHASE 3 VALIDATION CHECK")
    print("=" * 60)
    print("\n1. Checking Phase 3 files...")
    
    files = {
        "src/repositories/blocklist_repository.py": "Blocklist repository",
        "src/services/eligibility_service.py": "Eligibility service",
        "tests/unit/test_phase3_eligibility.py": "Phase 3 tests",
        "data/blocklist.txt": "Blocklist data",
    }
    
    all_exist = True
    for file, description in files.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file:50s} - {description}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_imports():
    """Test that Phase 3 modules can be imported."""
    print("\n2. Testing module imports...")
    
    modules = [
        ("src.repositories.blocklist_repository", "BlocklistRepository"),
        ("src.services.eligibility_service", "EligibilityService"),
    ]
    
    all_imported = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name:45s} - {description}")
        except Exception as e:
            print(f"   ❌ {module_name:45s} - {description}")
            print(f"      Error: {e}")
            all_imported = False
    
    return all_imported


async def test_eligibility_service():
    """Test the eligibility service with sample queries."""
    print("\n3. Testing EligibilityService functionality...")
    
    try:
        from src.repositories.blocklist_repository import BlocklistRepository
        from src.services.eligibility_service import EligibilityService
        
        # Initialize service
        blocklist_repo = BlocklistRepository("data/blocklist.txt")
        service = EligibilityService(blocklist_repo)
        
        # Test cases with expected score ranges
        test_cases = [
            ("I want to commit suicide", 0.0, 0.0, "Blocked content"),
            ("Best running shoes for marathon", 0.8, 1.0, "Commercial intent"),
            ("What is the history of the marathon?", 0.7, 0.85, "Informational"),
            ("I just got fired from my job", 0.3, 0.5, "Sensitive content"),
        ]
        
        all_passed = True
        for query, min_score, max_score, description in test_cases:
            score = await service.score(query)
            passed = min_score <= score <= max_score
            status = "✅" if passed else "❌"
            print(f"   {status} {description:20s} - Score: {score:.2f} (expected {min_score:.2f}-{max_score:.2f})")
            print(f"      Query: '{query}'")
            if not passed:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Error testing eligibility service: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_blocklist_loading():
    """Test that blocklist loads correctly."""
    print("\n4. Testing blocklist loading...")
    
    try:
        from src.repositories.blocklist_repository import BlocklistRepository
        
        repo = BlocklistRepository("data/blocklist.txt")
        count = repo.get_blocked_terms_count()
        
        if count > 0:
            print(f"   ✅ Loaded {count} blocked terms")
            
            # Test a few known blocked terms
            test_terms = [
                ("suicide", True),
                ("running shoes", False),
                ("porn", True),
            ]
            
            all_correct = True
            for term, should_be_blocked in test_terms:
                is_blocked = repo.contains_blocked_content(term)
                if is_blocked == should_be_blocked:
                    status = "✅"
                else:
                    status = "❌"
                    all_correct = False
                print(f"   {status} '{term}' - Blocked: {is_blocked} (expected: {should_be_blocked})")
            
            return all_correct
        else:
            print(f"   ❌ No blocked terms loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading blocklist: {e}")
        return False


def run_unit_tests():
    """Run Phase 3 unit tests."""
    print("\n5. Running Phase 3 unit tests...")
    
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/unit/test_phase3_eligibility.py", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("   ✅ All unit tests passed")
        # Print summary line
        for line in result.stdout.split('\n'):
            if 'passed' in line and '=' in line:
                print(f"      {line.strip()}")
        return True
    else:
        print("   ❌ Some unit tests failed")
        print(result.stdout)
        return False


def main():
    """Run all Phase 3 validation checks."""
    results = []
    
    # File checks
    results.append(("File existence", check_phase3_files()))
    
    # Import checks
    results.append(("Module imports", check_imports()))
    
    # Blocklist loading
    results.append(("Blocklist loading", check_blocklist_loading()))
    
    # Eligibility service functionality
    results.append(("Eligibility service", asyncio.run(test_eligibility_service())))
    
    # Unit tests
    results.append(("Unit tests", run_unit_tests()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10s} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 Phase 3 validation PASSED! All checks successful.")
        print("\nPhase 3 Components:")
        print("  - BlocklistRepository: Safety blocklist data access")
        print("  - EligibilityService: Ad eligibility scoring (0.0-1.0)")
        print("  - Comprehensive unit tests with 16 test cases")
        return 0
    else:
        print("\n❌ Phase 3 validation FAILED. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

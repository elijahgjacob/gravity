"""Phase 1 Validation Script - Quick sanity check for Phase 1 setup."""

import json
import os
import sys
from pathlib import Path


# Change to project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


def check_files():
    """Check that all required files exist."""
    print("=" * 60)
    print("PHASE 1 VALIDATION CHECK")
    print("=" * 60)
    print("\n1. Checking required files...")
    
    files = {
        "requirements.txt": "Dependencies file",
        "data/taxonomy.json": "Category taxonomy",
        "data/blocklist.txt": "Safety blocklist",
        "src/core/config.py": "Configuration module",
        "scripts/generate_data.py": "Data generator",
        ".gitignore": "Git ignore file",
        "README.md": "Documentation",
        "pytest.ini": "Test configuration",
    }
    
    all_exist = True
    for file, description in files.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file:30s} - {description}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_taxonomy():
    """Validate taxonomy structure."""
    print("\n2. Validating taxonomy...")
    
    try:
        with open("data/taxonomy.json") as f:
            taxonomy = json.load(f)
        
        print(f"   ✅ Total categories: {len(taxonomy)}")
        
        # Check structure
        sample_cat = list(taxonomy.keys())[0]
        sample_data = taxonomy[sample_cat]
        
        if "keywords" in sample_data and "related" in sample_data:
            print(f"   ✅ Structure valid (keywords + related fields)")
        else:
            print(f"   ❌ Invalid structure")
            return False
        
        # Show sample
        print(f"   📋 Sample: '{sample_cat}' has {len(sample_data['keywords'])} keywords")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_blocklist():
    """Validate blocklist."""
    print("\n3. Validating blocklist...")
    
    try:
        with open("data/blocklist.txt") as f:
            lines = f.readlines()
        
        terms = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
        categories = [line.strip() for line in lines if line.strip().startswith("#")]
        
        print(f"   ✅ Total terms: {len(terms)}")
        print(f"   ✅ Categories: {len(categories)}")
        
        # Check for critical terms
        content = " ".join(terms).lower()
        critical = ["suicide", "self harm", "porn", "nsfw"]
        found = sum(1 for term in critical if term in content)
        
        print(f"   ✅ Critical safety terms found: {found}/{len(critical)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_campaigns():
    """Check if campaigns were generated."""
    print("\n4. Checking campaign data...")
    
    if not os.path.exists("data/campaigns.jsonl"):
        print("   ⚠️  campaigns.jsonl not found - run: python scripts/generate_data.py")
        return False
    
    try:
        with open("data/campaigns.jsonl") as f:
            campaigns = [json.loads(line) for line in f]
        
        print(f"   ✅ Total campaigns: {len(campaigns)}")
        
        # Check first campaign structure
        required_fields = [
            "campaign_id", "title", "description", "category",
            "keywords", "targeting", "vertical", "budget", "cpc"
        ]
        
        first = campaigns[0]
        missing = [f for f in required_fields if f not in first]
        
        if not missing:
            print(f"   ✅ Campaign structure valid")
        else:
            print(f"   ❌ Missing fields: {missing}")
            return False
        
        # Show sample
        print(f"   📋 Sample: {first['campaign_id']} - {first['title'][:50]}...")
        print(f"   📋 Category: {first['category']}, Keywords: {len(first['keywords'])}")
        
        # Check verticals
        verticals = set(c["vertical"] for c in campaigns)
        print(f"   ✅ Verticals covered: {len(verticals)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_config():
    """Test configuration loading."""
    print("\n5. Testing configuration...")
    
    try:
        # Add project root to Python path
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        
        from src.core.config import settings
        
        print(f"   ✅ Configuration loaded successfully")
        print(f"   📋 Embedding model: {settings.EMBEDDING_MODEL}")
        print(f"   📋 Max campaigns: {settings.MAX_CAMPAIGNS_RETURNED}")
        print(f"   📋 Top-k candidates: {settings.TOP_K_CANDIDATES}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_tests():
    """Check test structure."""
    print("\n6. Checking test structure...")
    
    test_phases = ["phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "phase8"]
    
    for phase in test_phases:
        phase_dir = f"tests/{phase}"
        exists = os.path.exists(phase_dir)
        status = "✅" if exists else "❌"
        
        if phase == "phase1":
            # Count tests in phase1
            test_files = [f for f in os.listdir(phase_dir) if f.startswith("test_") and f.endswith(".py")]
            print(f"   {status} {phase_dir:20s} - {len(test_files)} test files")
        else:
            print(f"   {status} {phase_dir:20s} - (pending)")
    
    return True


def main():
    """Run all validation checks."""
    checks = [
        check_files(),
        check_taxonomy(),
        check_blocklist(),
        check_campaigns(),
        check_config(),
        check_tests(),
    ]
    
    print("\n" + "=" * 60)
    
    if all(checks[:5]):  # First 5 checks (excluding campaigns if not generated)
        print("✅ PHASE 1 SETUP COMPLETE!")
        print("\nNext steps:")
        if not checks[3]:  # campaigns not generated
            print("  1. Generate campaigns: python scripts/generate_data.py")
        print("  2. Run tests: pytest tests/phase1/ -v")
        print("  3. Ready for Phase 2 implementation!")
    else:
        print("❌ SOME CHECKS FAILED - Please review errors above")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == "__main__":
    main()

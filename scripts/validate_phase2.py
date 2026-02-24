"""Phase 2 Validation Script - Verify Phase 2 API setup."""

import os
import sys
from pathlib import Path

# Change to project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


def check_phase2_files():
    """Check that all Phase 2 files exist."""
    print("=" * 60)
    print("PHASE 2 VALIDATION CHECK")
    print("=" * 60)
    print("\n1. Checking Phase 2 files...")

    files = {
        "src/core/logging_config.py": "Logging configuration",
        "src/utils/timing.py": "Timing utilities",
        "src/api/models/requests.py": "Request models",
        "src/api/models/responses.py": "Response models",
        "src/core/dependencies.py": "Dependency injection",
        "src/api/routes/health.py": "Health routes",
        "src/api/routes/retrieval.py": "Retrieval routes",
        "src/api/main.py": "FastAPI application",
        "tests/phase2/test_models.py": "Model tests",
        "tests/phase2/test_api.py": "API tests",
    }

    all_exist = True
    for file, description in files.items():
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file:40s} - {description}")
        if not exists:
            all_exist = False

    return all_exist


def check_imports():
    """Test that Phase 2 modules can be imported."""
    print("\n2. Testing module imports...")

    modules = [
        ("src.core.logging_config", "Logging config"),
        ("src.utils.timing", "Timing utilities"),
        ("src.api.models.requests", "Request models"),
        ("src.api.models.responses", "Response models"),
        ("src.core.dependencies", "Dependencies"),
        ("src.api.routes.health", "Health routes"),
        ("src.api.routes.retrieval", "Retrieval routes"),
        ("src.api.main", "FastAPI app"),
    ]

    # Add project root to path
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    all_imported = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name:40s} - {description}")
        except Exception as e:
            print(f"   ❌ {module_name:40s} - Error: {e}")
            all_imported = False

    return all_imported


def check_fastapi_app():
    """Check FastAPI application configuration."""
    print("\n3. Validating FastAPI application...")

    try:
        from src.api.main import app

        print("   ✅ FastAPI app created")
        print(f"   📋 Title: {app.title}")
        print(f"   📋 Version: {app.version}")

        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/api/health", "/api/ready", "/api/retrieve"]

        for route in expected_routes:
            if route in routes:
                print(f"   ✅ Route: {route}")
            else:
                print(f"   ❌ Missing route: {route}")
                return False

        # Check middleware
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        print(f"   📋 Middleware: {', '.join(middleware_types) if middleware_types else 'None'}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_pydantic_models():
    """Validate Pydantic models."""
    print("\n4. Testing Pydantic models...")

    try:
        from src.api.models.requests import RetrievalRequest, UserContext
        from src.api.models.responses import Campaign, HealthResponse, RetrievalResponse

        # Test UserContext
        context = UserContext(age=25, gender="male")
        print("   ✅ UserContext model works")

        # Test RetrievalRequest
        request = RetrievalRequest(query="test query", context=context)
        print("   ✅ RetrievalRequest model works")

        # Test Campaign
        campaign = Campaign(
            campaign_id="test_123",
            relevance_score=0.95,
            title="Test Campaign",
            category="test",
            description="Test description",
            keywords=["test"],
        )
        print("   ✅ Campaign model works")

        # Test RetrievalResponse
        response = RetrievalResponse(
            ad_eligibility=0.85,
            extracted_categories=["test"],
            campaigns=[campaign],
            latency_ms=50.0,
        )
        print("   ✅ RetrievalResponse model works")

        # Test HealthResponse
        health = HealthResponse(status="healthy", version="1.0.0")
        print("   ✅ HealthResponse model works")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_logging():
    """Test logging configuration."""
    print("\n5. Testing logging setup...")

    try:
        from src.core.logging_config import get_logger, logger

        test_logger = get_logger("test_module")
        print("   ✅ Logger factory works")
        print(f"   📋 Default logger: {logger.name}")
        print(f"   📋 Test logger: {test_logger.name}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_timing_utilities():
    """Test timing utilities."""
    print("\n6. Testing timing utilities...")

    try:
        import time

        from src.utils.timing import LatencyTracker, timer

        # Test timer context manager
        with timer("test operation"):
            time.sleep(0.01)
        print("   ✅ Timer context manager works")

        # Test LatencyTracker
        tracker = LatencyTracker()
        tracker.start()
        time.sleep(0.01)
        tracker.record("test_component", 10.5)
        breakdown = tracker.get_breakdown()

        print("   ✅ LatencyTracker works")
        print(f"   📋 Total time: {breakdown['total_ms']:.2f}ms")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def run_phase2_tests():
    """Run Phase 2 test suite."""
    print("\n7. Running Phase 2 tests...")

    try:
        import subprocess

        result = subprocess.run(
            ["pytest", "tests/phase2/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Parse output for test count
        output = result.stdout
        if "passed" in output:
            # Extract test count
            for line in output.split("\n"):
                if "passed" in line:
                    print(f"   ✅ {line.strip()}")
                    break
            return result.returncode == 0
        else:
            print("   ❌ Tests failed")
            print(output)
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Tests timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error running tests: {e}")
        return False


def check_api_endpoints():
    """Check if API endpoints are defined correctly."""
    print("\n8. Checking API endpoint definitions...")

    try:
        from src.api.routes import health, retrieval

        # Check health router
        health_routes = [route.path for route in health.router.routes]
        print(f"   ✅ Health routes: {health_routes}")

        # Check retrieval router
        retrieval_routes = [route.path for route in retrieval.router.routes]
        print(f"   ✅ Retrieval routes: {retrieval_routes}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all validation checks."""
    checks = [
        check_phase2_files(),
        check_imports(),
        check_fastapi_app(),
        check_pydantic_models(),
        check_logging(),
        check_timing_utilities(),
        run_phase2_tests(),
        check_api_endpoints(),
    ]

    print("\n" + "=" * 60)

    if all(checks):
        print("✅ PHASE 2 SETUP COMPLETE!")
        print("\nNext steps:")
        print("  1. Start server: uvicorn src.api.main:app --reload")
        print("  2. Test API: python scripts/test_api_server.py")
        print("  3. View docs: http://localhost:8000/docs")
        print("  4. Ready for Phase 3 implementation!")
    else:
        print("❌ SOME CHECKS FAILED - Please review errors above")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()

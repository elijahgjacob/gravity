#!/usr/bin/env python
"""Test script to verify Graphiti and Neo4j are working."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.dependencies import init_dependencies, get_dependencies_status, shutdown_dependencies
from src.core.config import settings


async def test_graphiti_connection():
    """Test Graphiti and Neo4j connection."""
    print("=" * 60)
    print("Testing Graphiti + Neo4j Connection")
    print("=" * 60)
    print()
    
    # Print configuration
    print("Configuration:")
    print(f"  GRAPHITI_ENABLED: {settings.GRAPHITI_ENABLED}")
    print(f"  NEO4J_URI: {settings.GRAPHITI_NEO4J_URI}")
    print(f"  NEO4J_USER: {settings.GRAPHITI_NEO4J_USER}")
    print(f"  LLM_MODEL: {settings.GRAPHITI_LLM_MODEL}")
    print(f"  NAMESPACE: {settings.GRAPHITI_NAMESPACE}")
    print()
    
    if not settings.GRAPHITI_ENABLED:
        print("⚠️  GRAPHITI_ENABLED is False in .env")
        print("   Set GRAPHITI_ENABLED=true to enable Graphiti")
        return False
    
    if not settings.OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY is not set in .env")
        print("   Get a key from: https://openrouter.ai/")
        return False
    
    print("Initializing dependencies...")
    try:
        await init_dependencies()
        print("✓ Dependencies initialized")
        print()
        
        # Get status
        status = get_dependencies_status()
        
        print("Dependency Status:")
        print(f"  Initialized: {status['initialized']}")
        print(f"  Repositories:")
        for repo, status_val in status['repositories'].items():
            symbol = "✓" if status_val else "✗"
            print(f"    {symbol} {repo}: {status_val}")
        
        print()
        
        if status['repositories'].get('graphiti'):
            print("=" * 60)
            print("✅ SUCCESS! Graphiti + Neo4j are working!")
            print("=" * 60)
            print()
            print("Next Steps:")
            print("  1. Start your API server:")
            print("     uvicorn src.api.main:app --reload")
            print()
            print("  2. Make a request:")
            print("     curl -X POST http://localhost:8000/api/retrieve \\")
            print("       -H 'Content-Type: application/json' \\")
            print("       -d '{\"query\": \"running shoes\", \"context\": null}'")
            print()
            print("  3. Check Neo4j Browser:")
            print("     http://localhost:7474")
            print("     Username: neo4j")
            print("     Password: password")
            print()
            print("  4. Query the graph:")
            print("     MATCH (n) RETURN n LIMIT 25")
            print()
            return True
        else:
            print("=" * 60)
            print("❌ FAILED: Graphiti did not initialize")
            print("=" * 60)
            print()
            print("Troubleshooting:")
            print("  1. Check Neo4j is running:")
            print("     docker ps | grep neo4j")
            print()
            print("  2. Check Neo4j logs:")
            print("     docker logs gravity-neo4j")
            print()
            print("  3. Test Neo4j connection:")
            print("     curl http://localhost:7474")
            print()
            print("  4. Check API logs for errors")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure Neo4j is running:")
        print("     ./scripts/start_graphiti.sh")
        print()
        print("  2. Check .env configuration")
        print("  3. Verify OpenRouter API key is valid")
        return False
    finally:
        await shutdown_dependencies()


async def main():
    success = await test_graphiti_connection()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

"""Detailed test for profile inference with 5+ queries to trigger analysis."""

import asyncio
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"


async def test_marathon_with_5_queries():
    """Test marathon scenario with 5 queries to trigger analysis."""
    print("\n" + "="*80)
    print("MARATHON PLANNING - 5 QUERY TEST")
    print("="*80)
    
    user_id = f"marathon_user_{datetime.now().strftime('%H%M%S')}"
    session_id = f"sess_{datetime.now().strftime('%H%M%S')}"
    
    print(f"\nUser ID: {user_id}")
    print(f"Session ID: {session_id}\n")
    
    queries = [
        ("best marathon running shoes for training", "Query 1: Marathon shoes"),
        ("Boston weather in April", "Query 2: Boston weather"),
        ("hotels near Boston Marathon finish line", "Query 3: Boston hotels"),
        ("marathon training schedule 16 weeks", "Query 4: Training plan"),
        ("running gear for cold weather", "Query 5: Running gear - TRIGGERS ANALYSIS"),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, (query, label) in enumerate(queries, 1):
            print(f"{label}")
            print("-" * 80)
            
            response = await client.post(
                f"{API_URL}/api/retrieve",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id,
                    "context": {
                        "age": 30,
                        "gender": "male",
                        "location": "San Francisco, CA",
                        "interests": ["fitness", "running"]
                    }
                }
            )
            
            result = response.json()
            print(f"  Categories: {result['extracted_categories'][:5]}")
            print(f"  Latency: {result['latency_ms']:.2f}ms")
            
            if i == 5:
                print(f"  ⚡ Analysis should be triggered after this query!")
            
            print()
            await asyncio.sleep(1)
        
        # Wait for analysis to complete
        print("⏳ Waiting 3 seconds for background analysis...")
        await asyncio.sleep(3)
        
        # Query 6: Check for inferred categories
        print("\nQuery 6: Test query (should include inferred categories)")
        print("-" * 80)
        
        response = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "best running watches",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                }
            }
        )
        
        result = response.json()
        categories = result['extracted_categories']
        print(f"  Categories: {categories}")
        print(f"  Latency: {result['latency_ms']:.2f}ms")
        
        # Check for inferred categories
        inferred_cats = ["airfare", "travel_packages", "car_rental", "travel_insurance", "event_tickets"]
        found_inferred = [cat for cat in inferred_cats if cat in categories]
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        if found_inferred:
            print(f"✅ SUCCESS! Inferred categories detected: {found_inferred}")
            print(f"   The system learned from the query pattern!")
        else:
            print(f"⚠️  No inferred categories found")
            print(f"   All categories: {categories}")
            print(f"\n   Possible reasons:")
            print(f"   1. Pattern confidence below threshold (0.75)")
            print(f"   2. Location extraction failed")
            print(f"   3. Time window too strict")
            print(f"   4. Analysis still running (try waiting longer)")


async def test_with_debug_info():
    """Test with health check to see profile stats."""
    print("\n" + "="*80)
    print("SYSTEM STATUS CHECK")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_URL}/api/health")
        health = response.json()
        
        print(f"\nAPI Status: {health['status']}")
        print(f"Version: {health['version']}")
        
        if 'dependencies' in health:
            deps = health['dependencies']
            print(f"\nProfile System:")
            print(f"  Profile Repo: {'✓' if deps.get('profile') else '✗'}")
            print(f"  Profile Analyzer: {'✓' if deps.get('profile_analyzer') else '✗'}")
            print(f"  Graphiti: {'✓' if deps.get('graphiti') else '✗'}")


async def main():
    """Run tests."""
    print("\n" + "="*80)
    print("PROFILE INFERENCE SYSTEM - DETAILED TEST")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check system status
    await test_with_debug_info()
    
    # Run marathon test
    await test_marathon_with_5_queries()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

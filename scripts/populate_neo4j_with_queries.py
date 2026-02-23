"""
Script to populate Neo4j with conversational queries for intent evolution testing.

This script sends realistic conversation flows to the API to demonstrate
how Graphiti records intent progression and builds the knowledge graph.
"""

import asyncio
import httpx
import time
from datetime import datetime
from typing import List, Dict

API_BASE_URL = "http://localhost:8000"


# Conversation scenarios demonstrating intent progression
CONVERSATIONS = [
    {
        "session_id": "session_marathon_runner_001",
        "user_context": {"age": 30, "gender": "male", "location": "San Francisco, CA"},
        "queries": [
            "I'm thinking about running shoes",
            "I need them for marathon training",
            "What's good for long distance running?",
            "I'm training for my first marathon in 3 months",
            "What's the best value for marathon shoes under $150?",
            "Where can I buy Nike Pegasus 40?"
        ]
    },
    {
        "session_id": "session_casual_runner_002",
        "user_context": {"age": 25, "gender": "female", "location": "New York, NY"},
        "queries": [
            "running shoes for beginners",
            "I want to start jogging",
            "comfortable shoes for 5k runs",
            "what are good entry-level running shoes?"
        ]
    },
    {
        "session_id": "session_serious_athlete_003",
        "user_context": {"age": 28, "gender": "male", "location": "Austin, TX"},
        "queries": [
            "professional running shoes",
            "I need carbon plate shoes for racing",
            "comparing Nike Vaporfly vs Adidas Adizero",
            "best racing shoes for sub-3 hour marathon",
            "where to get the latest Vaporfly Next% 3"
        ]
    },
    {
        "session_id": "session_trail_runner_004",
        "user_context": {"age": 35, "gender": "female", "location": "Denver, CO"},
        "queries": [
            "trail running shoes",
            "shoes for mountain running",
            "I need good grip for rocky terrain",
            "waterproof trail shoes",
            "Salomon vs Hoka for trail running"
        ]
    },
    {
        "session_id": "session_budget_shopper_005",
        "user_context": {"age": 22, "gender": "male", "location": "Chicago, IL"},
        "queries": [
            "cheap running shoes",
            "affordable shoes for running",
            "best budget running shoes under $80",
            "are there any sales on running shoes?"
        ]
    },
    {
        "session_id": "session_injury_recovery_006",
        "user_context": {"age": 40, "gender": "female", "location": "Seattle, WA"},
        "queries": [
            "running shoes for knee pain",
            "I'm recovering from a running injury",
            "shoes with good cushioning for joint support",
            "best shoes for plantar fasciitis",
            "Hoka Bondi for injury recovery"
        ]
    },
    {
        "session_id": "session_gym_goer_007",
        "user_context": {"age": 26, "gender": "male", "location": "Los Angeles, CA"},
        "queries": [
            "shoes for gym workouts",
            "I do cardio and weights",
            "cross-training shoes",
            "versatile athletic shoes"
        ]
    },
    {
        "session_id": "session_fashion_conscious_008",
        "user_context": {"age": 24, "gender": "female", "location": "Miami, FL"},
        "queries": [
            "stylish running shoes",
            "running shoes that look good",
            "trendy athletic shoes",
            "Nike or Adidas for style and performance"
        ]
    }
]


async def send_query(client: httpx.AsyncClient, query: str, session_id: str, context: Dict) -> Dict:
    """Send a single query to the API."""
    payload = {
        "query": query,
        "session_id": session_id,
        "context": context
    }
    
    try:
        response = await client.post(f"{API_BASE_URL}/api/retrieve", json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"❌ Error sending query: {e}")
        return None


async def run_conversation(client: httpx.AsyncClient, conversation: Dict) -> None:
    """Run a complete conversation flow."""
    session_id = conversation["session_id"]
    context = conversation["user_context"]
    queries = conversation["queries"]
    
    print(f"\n{'='*80}")
    print(f"🗣️  Starting Conversation: {session_id}")
    print(f"👤 User: {context.get('gender', 'unknown')}, {context.get('age', 'unknown')} years old, {context.get('location', 'unknown')}")
    print(f"📊 Total queries: {len(queries)}")
    print(f"{'='*80}\n")
    
    for i, query in enumerate(queries, 1):
        print(f"Query {i}/{len(queries)}: \"{query}\"")
        
        start_time = time.perf_counter()
        result = await send_query(client, query, session_id, context)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if result:
            print(f"  ✅ Response: {result.get('ad_eligibility', 0):.2f} eligibility, "
                  f"{len(result.get('campaigns', []))} campaigns, "
                  f"{latency_ms:.1f}ms latency")
            print(f"  📂 Categories: {', '.join(result.get('extracted_categories', []))}")
            
            # Show top 3 campaigns
            campaigns = result.get('campaigns', [])[:3]
            if campaigns:
                print(f"  🎯 Top campaigns:")
                for j, campaign in enumerate(campaigns, 1):
                    print(f"     {j}. {campaign.get('title', 'Unknown')} "
                          f"(relevance: {campaign.get('relevance_score', 0):.2f})")
        else:
            print(f"  ❌ Failed to get response")
        
        # Small delay between queries to simulate natural conversation
        await asyncio.sleep(1)
    
    print(f"\n✅ Conversation {session_id} completed!\n")


async def check_api_health() -> bool:
    """Check if the API is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/health", timeout=5.0)
            return response.status_code == 200
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False


async def get_dependencies_status() -> Dict:
    """Get the status of dependencies including Graphiti."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/ready", timeout=5.0)
            return response.json()
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
        return {}


async def main():
    """Main function to run all conversations."""
    print("\n" + "="*80)
    print("🚀 Neo4j Population Script - Intent Evolution Tracking Demo")
    print("="*80)
    
    # Check API health
    print("\n📡 Checking API health...")
    if not await check_api_health():
        print("❌ API is not running. Please start the server first:")
        print("   uvicorn src.api.main:app --reload")
        return
    print("✅ API is running!")
    
    # Check dependencies status
    print("\n📊 Checking dependencies status...")
    status = await get_dependencies_status()
    if status:
        deps = status.get('dependencies', {})
        print(f"  Graphiti: {'✅ Enabled' if deps.get('graphiti') else '❌ Disabled'}")
        print(f"  Session State: {'✅ Enabled' if deps.get('session_state') else '❌ Disabled'}")
        
        if not deps.get('graphiti'):
            print("\n⚠️  WARNING: Graphiti is not enabled!")
            print("   Neo4j will not be populated without Graphiti.")
            print("   Make sure:")
            print("   1. Neo4j is running (docker-compose up -d)")
            print("   2. GRAPHITI_ENABLED=true in .env")
            print("   3. API has been restarted")
            
            response = input("\nContinue anyway? (y/N): ")
            if response.lower() != 'y':
                return
    
    # Run conversations
    print(f"\n🎬 Running {len(CONVERSATIONS)} conversation scenarios...")
    print("   This will take a few minutes...\n")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        for conversation in CONVERSATIONS:
            await run_conversation(client, conversation)
    
    total_time = time.time() - start_time
    total_queries = sum(len(c['queries']) for c in CONVERSATIONS)
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Completed {len(CONVERSATIONS)} conversations")
    print(f"✅ Sent {total_queries} total queries")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"⚡ Average: {total_time/total_queries:.2f} seconds per query")
    
    print("\n🔍 What happened:")
    print("  1. Each query was sent to the API with a session_id")
    print("  2. Session state tracked query history in memory")
    print("  3. Graphiti recorded each query with conversational context")
    print("  4. Neo4j now contains:")
    print("     - Query episodes with session history")
    print("     - Conversation dynamics (time spans, topic shifts)")
    print("     - User context and campaign results")
    print("     - Intent signals extracted by LLM")
    
    print("\n🔎 Next steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Run Cypher queries to explore the graph:")
    print("     - MATCH (n) RETURN n LIMIT 25")
    print("     - MATCH (n) WHERE n.name CONTAINS 'session_marathon' RETURN n")
    print("  3. Check session state via API:")
    print("     - GET http://localhost:8000/status")
    print("  4. Query intent insights (once implemented):")
    print("     - Use IntentEvolutionService to analyze trajectories")
    
    print("\n✨ Neo4j population complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

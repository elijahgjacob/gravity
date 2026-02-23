#!/bin/bash

# Demo script showing real-time intent evolution tracking
# This simulates a user's journey from awareness to purchase

API_URL="http://localhost:8000"
SESSION_ID="demo_session_$(date +%s)"

echo ""
echo "================================================================================"
echo "🎯 Real-Time Intent Evolution Demo"
echo "================================================================================"
echo ""
echo "Session ID: $SESSION_ID"
echo "API: $API_URL"
echo ""
echo "This demo simulates a user's journey from browsing to purchase."
echo "Watch how the intent signals, stage, and purchase readiness evolve!"
echo ""

# Function to make a query and show intent insights
make_query() {
    local query="$1"
    local query_num="$2"
    
    echo "--------------------------------------------------------------------------------"
    echo "Query #$query_num: \"$query\""
    echo "--------------------------------------------------------------------------------"
    
    # Make the retrieval request
    response=$(curl -s -X POST "$API_URL/api/retrieve" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"$SESSION_ID\",
            \"context\": {
                \"age\": 32,
                \"gender\": \"female\",
                \"location\": \"Boston, MA\"
            }
        }")
    
    # Extract key metrics
    ad_eligibility=$(echo "$response" | jq -r '.ad_eligibility // 0')
    campaign_count=$(echo "$response" | jq -r '.campaigns | length // 0')
    categories=$(echo "$response" | jq -r '.extracted_categories | join(", ") // "none"')
    
    echo "  📊 Response:"
    echo "     Ad Eligibility: $ad_eligibility"
    echo "     Campaigns Returned: $campaign_count"
    echo "     Categories: $categories"
    
    # Small delay to ensure Graphiti records the episode
    sleep 2
    
    # Now query the intent insights via Neo4j MCP
    echo ""
    echo "  🧠 Intent Analysis (from Neo4j):"
    
    # Use Python to query intent service
    python3 -c "
import asyncio
import sys
import os
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def get_insights():
    repo = GraphitiRepository(
        neo4j_uri=os.getenv('GRAPHITI_NEO4J_URI'),
        neo4j_user=os.getenv('GRAPHITI_NEO4J_USER'),
        neo4j_password=os.getenv('GRAPHITI_NEO4J_PASSWORD'),
        openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
        llm_model=os.getenv('GRAPHITI_LLM_MODEL'),
        namespace=os.getenv('GRAPHITI_NAMESPACE')
    )
    
    try:
        await repo.initialize()
        service = IntentEvolutionService(repo)
        insights = await service.get_intent_insights('$SESSION_ID')
        
        print(f'     Current Stage: {insights[\"current_stage\"]}')
        print(f'     Purchase Readiness: {insights[\"readiness_score\"]:.2f}')
        print(f'     Recommended Strategy: {insights[\"recommended_strategy\"]}')
        print(f'     Query Count: {insights[\"query_count\"]}')
        print(f'     Velocity: {insights[\"velocity\"]:.2f} stages/hour')
        
        signals = insights.get('signals', {})
        if signals.get('urgency_indicators'):
            print(f'     🚨 Urgency Signals: {len(signals[\"urgency_indicators\"])}')
        if signals.get('budget_mentions'):
            print(f'     💰 Budget Mentions: {len(signals[\"budget_mentions\"])}')
        if signals.get('specific_products'):
            print(f'     🎯 Specific Products: {len(signals[\"specific_products\"])}')
        print(f'     📊 Specificity Level: {signals.get(\"specificity_level\", \"low\")}')
        
    finally:
        await repo.shutdown()

asyncio.run(get_insights())
" 2>/dev/null
    
    echo ""
    sleep 1
}

# Scenario: User journey from awareness to purchase
echo "🎬 Starting User Journey Simulation..."
echo ""
sleep 2

# Query 1: Initial awareness - vague interest
make_query "running shoes" 1

# Query 2: Research phase - gathering information
make_query "best running shoes for beginners" 2

# Query 3: Consideration - getting specific
make_query "Nike vs Adidas running shoes" 3

# Query 4: High intent - urgency + specificity
make_query "I need Nike Pegasus 40 for marathon training" 4

# Query 5: Purchase intent - budget + specific product
make_query "where can I buy Nike Pegasus 40 under $150" 5

echo "================================================================================"
echo "✅ Demo Complete!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - Started with vague awareness query: 'running shoes'"
echo "  - Progressed through research: 'best running shoes for beginners'"
echo "  - Entered consideration: 'Nike vs Adidas'"
echo "  - Showed urgency: 'I need Nike Pegasus 40 for marathon training'"
echo "  - Ready to purchase: 'where can I buy Nike Pegasus 40 under \$150'"
echo ""
echo "🔍 Check Neo4j Browser to see the knowledge graph:"
echo "   http://localhost:7474"
echo ""
echo "Query to visualize this session:"
echo "   MATCH (e:Episodic)-[:MENTIONS]->(ent:Entity)"
echo "   WHERE e.name CONTAINS '$SESSION_ID'"
echo "   RETURN e, ent LIMIT 50"
echo ""

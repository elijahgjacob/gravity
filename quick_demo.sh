#!/bin/bash

# Quick visual demo showing intent evolution
SESSION_ID="quick_demo_$(date +%s)"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🎯 INTENT EVOLUTION LIVE DEMO                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Session: $SESSION_ID"
echo ""

# Function to make query and show results
query() {
    local num=$1
    local text=$2
    local expected_stage=$3
    local expected_readiness=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Query #$num: \"$text\""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Make API call
    response=$(curl -s -X POST http://localhost:8000/api/retrieve \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$text\",
            \"session_id\": \"$SESSION_ID\",
            \"context\": {\"age\": 28, \"gender\": \"male\", \"location\": \"NYC\"}
        }")
    
    eligibility=$(echo "$response" | jq -r '.ad_eligibility')
    campaigns=$(echo "$response" | jq -r '.campaigns | length')
    
    echo "   API Response:"
    echo "   ├─ Ad Eligibility: $eligibility"
    echo "   └─ Campaigns: $campaigns"
    echo ""
    
    # Wait for Graphiti
    sleep 3
    
    # Get intent analysis
    echo "   🧠 Intent Analysis:"
    python3 -c "
import asyncio, sys, os
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def analyze():
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
        
        # Format stage with emoji
        stage_emoji = {
            'AWARENESS': '🔍',
            'RESEARCH': '📚',
            'CONSIDERATION': '🤔',
            'PURCHASE': '🛒'
        }
        
        stage = insights['current_stage']
        readiness = insights['readiness_score']
        strategy = insights['recommended_strategy']
        
        print(f\"   ├─ Stage: {stage_emoji.get(stage, '•')} {stage}\")
        print(f\"   ├─ Purchase Readiness: {readiness:.2f} {'█' * int(readiness * 10)}\")
        print(f\"   ├─ Strategy: {strategy}\")
        print(f\"   └─ Velocity: {insights['velocity']:.1f} stages/hr\")
        
        signals = insights.get('signals', {})
        if signals.get('urgency_indicators') or signals.get('budget_mentions') or signals.get('specific_products'):
            print(\"   \")
            print(\"   Signals:\")
            if signals.get('urgency_indicators'):
                print(f\"   🚨 Urgency detected\")
            if signals.get('budget_mentions'):
                print(f\"   💰 Budget mentioned\")
            if signals.get('specific_products'):
                print(f\"   🎯 Specific product: {signals['specific_products'][0]}\")
        
    finally:
        await repo.shutdown()

asyncio.run(analyze())
" 2>/dev/null
    
    echo ""
    sleep 1
}

# Run the demo
query 1 "running shoes" "AWARENESS" "0.20"
query 2 "I need running shoes for marathon training" "CONSIDERATION" "0.70"
query 3 "Nike Pegasus 40 vs Brooks Ghost" "CONSIDERATION" "0.80"
query 4 "where to buy Nike Pegasus 40 under 150" "PURCHASE" "1.00"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                           ✅ DEMO COMPLETE                                 ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "   Query 1: Generic search → AWARENESS stage (0.20 readiness)"
echo "   Query 2: Added urgency → CONSIDERATION stage (0.70 readiness)"
echo "   Query 3: Comparing products → CONSIDERATION/PURCHASE (0.80+ readiness)"
echo "   Query 4: Ready to buy → PURCHASE stage (1.00 readiness)"
echo ""
echo "🔍 View in Neo4j Browser: http://localhost:7474"
echo ""
echo "   MATCH (e:Episodic) WHERE e.name CONTAINS '$SESSION_ID'"
echo "   RETURN e ORDER BY e.created_at"
echo ""

# Live Intent Evolution Demo - Manual Commands

Run these curl commands one by one to see how intent evolves in real-time!

## Setup

```bash
# Set your session ID
export SESSION_ID="live_demo_$(date +%s)"
echo "Session ID: $SESSION_ID"
```

---

## Query 1: Awareness Stage (Generic Interest)

```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"running shoes\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"age\": 32,
      \"gender\": \"female\",
      \"location\": \"Boston, MA\"
    }
  }" | jq '{
    ad_eligibility,
    campaign_count: (.campaigns | length),
    categories: .extracted_categories
  }'
```

**Expected:**
- Ad Eligibility: ~0.75
- Stage: AWARENESS
- Purchase Readiness: ~0.20
- Strategy: educational

---

## Query 2: Research Stage (Gathering Info)

Wait 3 seconds for Graphiti to record, then:

```bash
sleep 3

curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"best running shoes for beginners\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"age\": 32,
      \"gender\": \"female\",
      \"location\": \"Boston, MA\"
    }
  }" | jq '{
    ad_eligibility,
    campaign_count: (.campaigns | length),
    categories: .extracted_categories
  }'
```

**Expected:**
- Ad Eligibility: ~0.95
- Stage: CONSIDERATION
- Purchase Readiness: ~0.70
- Strategy: comparison

---

## Query 3: Consideration Stage (Comparing Options)

```bash
sleep 3

curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Nike vs Adidas running shoes for marathon\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"age\": 32,
      \"gender\": \"female\",
      \"location\": \"Boston, MA\"
    }
  }" | jq '{
    ad_eligibility,
    campaign_count: (.campaigns | length),
    categories: .extracted_categories
  }'
```

**Expected:**
- Ad Eligibility: ~0.95
- Stage: PURCHASE
- Purchase Readiness: ~1.00
- Strategy: conversion
- Velocity: High (rapid progression)

---

## Query 4: Purchase Intent (Urgency + Specific Product)

```bash
sleep 3

curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"I need Nike Pegasus 40 for marathon training\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"age\": 32,
      \"gender\": \"female\",
      \"location\": \"Boston, MA\"
    }
  }" | jq '{
    ad_eligibility,
    campaign_count: (.campaigns | length),
    categories: .extracted_categories
  }'
```

**Expected:**
- Ad Eligibility: ~0.75
- Stage: PURCHASE
- Purchase Readiness: 1.00
- **Signals Detected:**
  - ✅ Urgency: "I need"
  - ✅ Specific Product: "Nike Pegasus 40"
  - ✅ Specificity: medium

---

## Query 5: Ready to Buy (Budget + Location Intent)

```bash
sleep 3

curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"where can I buy Nike Pegasus 40 under 150 dollars\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"age\": 32,
      \"gender\": \"female\",
      \"location\": \"Boston, MA\"
    }
  }" | jq '{
    ad_eligibility,
    campaign_count: (.campaigns | length),
    categories: .extracted_categories
  }'
```

**Expected:**
- Ad Eligibility: ~0.95
- Stage: PURCHASE
- Purchase Readiness: 1.00
- **Signals Detected:**
  - ✅ Budget: "under 150 dollars"
  - ✅ Specific Product: "Nike Pegasus 40"
  - ✅ Location Intent: "where can I buy"
  - ✅ Specificity: medium

---

## Check Intent Insights (After All Queries)

```bash
# Wait for Graphiti to process all episodes
sleep 5

# Query intent insights using Neo4j MCP
python3 << 'EOF'
import asyncio
import os
import sys
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def main():
    session_id = os.getenv('SESSION_ID', 'live_demo_1771887729')
    
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
        
        print("\n" + "="*80)
        print("🧠 INTENT EVOLUTION ANALYSIS")
        print("="*80)
        
        trajectory = await service.get_session_intent_trajectory(session_id)
        
        print(f"\n📊 Session: {session_id}")
        print(f"   Query Count: {trajectory['query_count']}")
        print(f"   Time Span: {trajectory['time_span_minutes']:.2f} minutes")
        print(f"   Current Stage: {trajectory['current_stage']}")
        print(f"   Velocity: {trajectory['velocity']:.2f} stages/hour")
        
        if trajectory['stages']:
            print(f"\n   Stage Progression:")
            print(f"   {' → '.join(trajectory['stages'])}")
        
        if trajectory['progression']:
            print(f"\n   Stage Transitions:")
            for trans in trajectory['progression']:
                print(f"   - Query {trans['query_number']}: {trans['from']} → {trans['to']}")
        
        signals = trajectory['signals']
        print(f"\n🎯 Signals Detected:")
        print(f"   Urgency Indicators: {len(signals.get('urgency_indicators', []))}")
        if signals.get('urgency_indicators'):
            for sig in signals['urgency_indicators'][:3]:
                print(f"     - \"{sig}\"")
        
        print(f"   Budget Mentions: {len(signals.get('budget_mentions', []))}")
        if signals.get('budget_mentions'):
            for sig in signals['budget_mentions'][:3]:
                print(f"     - \"{sig}\"")
        
        print(f"   Specific Products: {len(signals.get('specific_products', []))}")
        if signals.get('specific_products'):
            for sig in signals['specific_products'][:3]:
                print(f"     - \"{sig}\"")
        
        print(f"   Specificity Level: {signals.get('specificity_level', 'low')}")
        print(f"   Hesitation Signals: {len(signals.get('hesitation_signals', []))}")
        
        insights = await service.get_intent_insights(session_id)
        
        print(f"\n💰 Purchase Readiness:")
        print(f"   Score: {insights['readiness_score']:.2f}")
        print(f"   Recommended Strategy: {insights['recommended_strategy']}")
        print(f"   Predicted Next Stage: {insights['next_stage']}")
        
        print("\n" + "="*80)
        
    finally:
        await repo.shutdown()

asyncio.run(main())
EOF
```

---

## Visualize in Neo4j Browser

1. Open: http://localhost:7474
2. Run this query:

```cypher
MATCH (e:Episodic)-[:MENTIONS]->(ent:Entity)
WHERE e.name CONTAINS 'live_demo'
RETURN e, ent
ORDER BY e.created_at ASC
LIMIT 50
```

---

## Alternative: Query Specific Session

To check a specific session's trajectory:

```bash
# Using Neo4j MCP directly
curl -X POST http://localhost:8000/api/intent/insights/$SESSION_ID
```

Or query Neo4j directly:

```cypher
MATCH (e:Episodic)
WHERE e.name CONTAINS '$SESSION_ID'
RETURN e.content, e.created_at, e.name
ORDER BY e.created_at ASC
```

---

## Understanding the Results

### Intent Stages
- **AWARENESS**: Generic browsing (eligibility < 0.5)
- **RESEARCH**: Gathering information (eligibility 0.5-0.74)
- **CONSIDERATION**: Comparing options (eligibility 0.75-0.89)
- **PURCHASE**: Ready to buy (eligibility ≥ 0.9)

### Purchase Readiness Score
- **0.0-0.4**: Educational content recommended
- **0.4-0.8**: Comparison/review content recommended
- **0.8-1.0**: Conversion-focused content recommended

### Velocity
- Measures how fast user progresses through stages
- High velocity (>100 stages/hour) = urgent buyer
- Low velocity (<10 stages/hour) = casual browser

### Signals
- **Urgency**: need, urgent, today, now, asap, soon
- **Budget**: $150, under $, budget, cheap, value
- **Specific Products**: Brand + model (Nike Pegasus 40)
- **Hesitation**: maybe, not sure, thinking about

---

## Clean Up

To clear the session from cache:

```python
python3 << 'EOF'
import asyncio
import os
import sys
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def main():
    session_id = os.getenv('SESSION_ID')
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
        service.clear_cache(session_id)
        print(f"✅ Cleared cache for session: {session_id}")
    finally:
        await repo.shutdown()

asyncio.run(main())
EOF
```

# Simple Curl Examples - Intent Evolution Demo

## Quick Test (Copy & Paste)

### 1. Set Session ID
```bash
export SESSION="test_$(date +%s)"
```

### 2. Query 1 - Awareness (Generic)
```bash
curl -s -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"running shoes\",
    \"session_id\": \"$SESSION\",
    \"context\": {\"age\": 28, \"gender\": \"male\"}
  }" | jq '{eligibility: .ad_eligibility, campaigns: (.campaigns|length)}'
```

**Result:** Eligibility ~0.75, Stage: AWARENESS 🔍

---

### 3. Query 2 - Research (Urgency Signal)
```bash
sleep 3
curl -s -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"I need running shoes for marathon training\",
    \"session_id\": \"$SESSION\",
    \"context\": {\"age\": 28, \"gender\": \"male\"}
  }" | jq '{eligibility: .ad_eligibility, campaigns: (.campaigns|length)}'
```

**Result:** Eligibility ~0.75, Stage: CONSIDERATION 🤔, Urgency detected! 🚨

---

### 4. Query 3 - Consideration (Comparing)
```bash
sleep 3
curl -s -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Nike Pegasus 40 vs Brooks Ghost\",
    \"session_id\": \"$SESSION\",
    \"context\": {\"age\": 28, \"gender\": \"male\"}
  }" | jq '{eligibility: .ad_eligibility, campaigns: (.campaigns|length)}'
```

**Result:** Eligibility ~0.95, Stage: CONSIDERATION/PURCHASE 🤔→🛒, Velocity increases!

---

### 5. Query 4 - Purchase (Budget + Product)
```bash
sleep 3
curl -s -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"where to buy Nike Pegasus 40 under 150\",
    \"session_id\": \"$SESSION\",
    \"context\": {\"age\": 28, \"gender\": \"male\"}
  }" | jq '{eligibility: .ad_eligibility, campaigns: (.campaigns|length)}'
```

**Result:** Eligibility ~0.95, Stage: PURCHASE 🛒, Readiness: 1.00! 💯

---

## Check Intent Analysis

After running all queries, check the intent trajectory:

```bash
sleep 5  # Wait for Graphiti to process

python3 << EOF
import asyncio, sys, os
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def main():
    session = os.getenv('SESSION', 'test_session')
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
        insights = await service.get_intent_insights(session)
        
        print(f"\n{'='*60}")
        print(f"🧠 INTENT ANALYSIS - Session: {session}")
        print(f"{'='*60}")
        print(f"Stage: {insights['current_stage']}")
        print(f"Purchase Readiness: {insights['readiness_score']:.2f}")
        print(f"Strategy: {insights['recommended_strategy']}")
        print(f"Velocity: {insights['velocity']:.1f} stages/hour")
        print(f"Query Count: {insights['query_count']}")
        
        signals = insights.get('signals', {})
        if any(signals.values()):
            print(f"\nSignals Detected:")
            if signals.get('urgency_indicators'):
                print(f"  🚨 Urgency: {len(signals['urgency_indicators'])} signals")
            if signals.get('budget_mentions'):
                print(f"  💰 Budget: {len(signals['budget_mentions'])} mentions")
            if signals.get('specific_products'):
                print(f"  🎯 Products: {signals['specific_products']}")
        print(f"{'='*60}\n")
        
    finally:
        await repo.shutdown()

asyncio.run(main())
EOF
```

---

## Direct Neo4j Query (via MCP)

Query the raw data:

```bash
# Using the Neo4j MCP server we installed
python3 << 'EOF'
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('GRAPHITI_NEO4J_URI'),
    auth=(os.getenv('GRAPHITI_NEO4J_USER'), os.getenv('GRAPHITI_NEO4J_PASSWORD'))
)

session_id = os.getenv('SESSION', 'test_session')

with driver.session() as session:
    result = session.run("""
        MATCH (e:Episodic)
        WHERE e.name CONTAINS $session_id
        RETURN e.name, e.content
        ORDER BY e.created_at ASC
    """, session_id=session_id)
    
    print(f"\n{'='*60}")
    print(f"📊 RAW NEO4J DATA - Session: {session_id}")
    print(f"{'='*60}\n")
    
    for i, record in enumerate(result, 1):
        print(f"Episode {i}: {record['e.name']}")
        content = record['e.content']
        # Extract just the query
        if 'Current Query:' in content:
            query = content.split('Current Query:')[1].split('\n')[0].strip()
            print(f"  Query: {query}")
        if 'Ad Eligibility:' in content:
            elig = content.split('Ad Eligibility:')[1].split('\n')[0].strip()
            print(f"  Eligibility: {elig}")
        print()

driver.close()
EOF
```

---

## Visual Progress Bar

See the readiness increase in real-time:

```bash
for i in {1..4}; do
    echo "Query $i..."
    # Run your curl command here
    sleep 3
    
    # Show readiness bar
    python3 << EOF
import asyncio, sys, os
sys.path.insert(0, '/Users/elijahgjacob/gravity')
from dotenv import load_dotenv
load_dotenv()
from src.repositories.graphiti_repository import GraphitiRepository
from src.services.intent_evolution_service import IntentEvolutionService

async def show_bar():
    session = os.getenv('SESSION')
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
        insights = await service.get_intent_insights(session)
        readiness = insights['readiness_score']
        bar = '█' * int(readiness * 20)
        print(f"Readiness: [{bar:<20}] {readiness:.2f}")
    finally:
        await repo.shutdown()

asyncio.run(show_bar())
EOF
done
```

---

## What to Watch For

### Stage Progression
- 🔍 **AWARENESS** → 📚 **RESEARCH** → 🤔 **CONSIDERATION** → 🛒 **PURCHASE**

### Readiness Score
- **0.20**: Just browsing
- **0.70**: Actively researching
- **0.95**: Comparing options
- **1.00**: Ready to buy NOW!

### Velocity
- **< 50**: Casual browser
- **50-200**: Engaged shopper
- **> 200**: Urgent buyer (hot lead!)

### Signals
- 🚨 **Urgency**: "I need", "urgent", "today"
- 💰 **Budget**: "$150", "under", "cheap"
- 🎯 **Product**: "Nike Pegasus 40", "Brooks Ghost"
- 🤔 **Hesitation**: "maybe", "not sure"

---

## Pro Tip

Run the quick demo script for a full automated demo:

```bash
./quick_demo.sh
```

Or use the detailed manual commands:

```bash
# See LIVE_DEMO_COMMANDS.md for step-by-step instructions
cat LIVE_DEMO_COMMANDS.md
```

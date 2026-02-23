# Graphiti Knowledge Graph Integration

## Overview

This document describes the Graphiti knowledge graph integration in the Ad Retrieval System. Graphiti provides a temporal knowledge graph that learns from user queries, campaign impressions, and interactions over time.

## Architecture

### Fire-and-Forget Pattern

The integration uses an **async fire-and-forget pattern** to ensure zero latency impact on retrieval:

```
┌─────────────────────────────────────────────────────────┐
│  User Request                                            │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│  Fast Retrieval Pipeline (24ms avg)                     │
│  • Eligibility scoring                                   │
│  • Category extraction                                   │
│  • Vector search                                         │
│  • Ranking                                               │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│  Return Response to User (24ms)                         │
└────────────┬────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────┐
             │                                             │
             ▼                                             ▼
   ┌─────────────────┐                          ┌──────────────────┐
   │  User receives  │                          │  Async Task      │
   │  response       │                          │  (background)    │
   └─────────────────┘                          └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │ Graphiti Service │
                                                │ Records Event    │
                                                └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │  Neo4j Graph DB  │
                                                │  + OpenRouter    │
                                                └──────────────────┘
```

### Components

1. **GraphitiRepository** (`src/repositories/graphiti_repository.py`)
   - Manages Neo4j connection
   - Configures OpenRouter LLM client
   - Handles episode creation and queries

2. **GraphitiService** (`src/services/graphiti_service.py`)
   - Builds structured episodes from query events
   - Records campaign impressions
   - Tracks user journeys

3. **Event Models** (`src/api/models/events.py`)
   - QueryEvent: Query + context + results
   - CampaignImpression: Campaign shown to user
   - UserSession: Session-level tracking

## Setup Guide

### Prerequisites

- Python 3.11+
- Neo4j 5.26+ (local or cloud)
- OpenRouter API key

### Step 1: Install Neo4j

**Option A: Docker (Recommended)**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_secure_password \
  -v $PWD/neo4j_data:/data \
  neo4j:5.26
```

Access Neo4j Browser at: http://localhost:7474

**Option B: Neo4j Desktop**

Download from: https://neo4j.com/download/

**Option C: Neo4j Aura (Cloud)**

Sign up at: https://neo4j.com/cloud/aura/

### Step 2: Get OpenRouter API Key

1. Sign up at: https://openrouter.ai/
2. Create an API key
3. Add credits to your account

### Step 3: Configure Environment

Update your `.env` file:

```env
GRAPHITI_ENABLED=true
GRAPHITI_NEO4J_URI=bolt://localhost:7687
GRAPHITI_NEO4J_USER=neo4j
GRAPHITI_NEO4J_PASSWORD=your_secure_password
OPENROUTER_API_KEY=sk-or-v1-your-key-here
GRAPHITI_LLM_MODEL=anthropic/claude-3.5-sonnet
GRAPHITI_NAMESPACE=ad_retrieval
```

### Step 4: Install Dependencies

```bash
pip install graphiti-core==0.28.1 neo4j==5.26.0
```

### Step 5: Start the API

```bash
uvicorn src.api.main:app --reload
```

You should see in the logs:
```
✓ Graphiti repository initialized (using OpenRouter)
```

## Configuration Options

### LLM Models

Graphiti supports any OpenRouter model. Recommended options:

| Model | Cost | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `anthropic/claude-3.5-sonnet` | $$$ | Fast | Excellent | Production (recommended) |
| `openai/gpt-4` | $$$$ | Medium | Excellent | High-quality extraction |
| `openai/gpt-3.5-turbo` | $ | Very Fast | Good | Cost-optimized |
| `google/gemini-pro` | $$ | Fast | Very Good | Balanced option |

### Neo4j Options

**Local Development:**
- URI: `bolt://localhost:7687`
- User: `neo4j`
- Password: Your chosen password

**Neo4j Aura (Cloud):**
- URI: `neo4j+s://xxxxx.databases.neo4j.io`
- User: `neo4j`
- Password: Generated password from Aura

**Docker Compose:**
```yaml
services:
  neo4j:
    image: neo4j:5.26
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

## What Gets Recorded

### Query Events

Each query generates an episode like:

```
User Query: "running shoes for marathon"
User Context: 30 years old, male, from San Francisco, CA, interested in fitness, running
Ad Eligibility: 0.95 (highly appropriate for ads)
Extracted Categories: running_shoes, marathon_gear, athletic_footwear
Top 3 campaigns shown:
1. Nike Premium Marathon Trainers (category: running_shoes, relevance: 0.94)
2. Adidas Ultra Boost Running Shoes (category: running_shoes, relevance: 0.92)
3. Brooks Ghost 15 Running Shoes (category: athletic_footwear, relevance: 0.90)
... and 7 more campaigns
```

### Knowledge Graph Structure

Graphiti automatically extracts entities and relationships:

**Entities:**
- Users (age, gender, location, interests)
- Queries (text, intent, categories)
- Campaigns (ID, title, category)
- Categories (product/service types)

**Relationships:**
- User → SEARCHED_FOR → Query
- Query → HAS_CATEGORY → Category
- Query → SHOWED_CAMPAIGN → Campaign
- Campaign → BELONGS_TO_CATEGORY → Category
- Query → FOLLOWED_BY → Query (temporal)

## Querying the Knowledge Graph

### Example: User Journey

```python
from src.repositories.graphiti_repository import GraphitiRepository

# Get user's query history
journey = await graphiti_repo.get_user_journey(
    user_id="user_123",
    limit=10
)

# Returns: List of queries in temporal order
# ["running shoes", "marathon training plan", "running watch", ...]
```

### Example: Campaign Relationships

```python
# Find campaigns that often appear together
related = await graphiti_repo.get_campaign_relationships(
    campaign_id="camp_123",
    relationship_type="co_occurrence",
    limit=10
)

# Returns: Campaigns frequently shown with camp_123
```

## Monitoring

### Logs

Graphiti operations are logged at DEBUG level:

```
2026-02-23 20:00:00 - DEBUG - Recording query event: 'running shoes for marathon...'
2026-02-23 20:00:00 - DEBUG - Query event recorded successfully: query_20260223_200000_123456
```

Errors are logged at WARNING level (non-critical):

```
2026-02-23 20:00:00 - WARNING - Graphiti recording failed (non-critical): Neo4j connection timeout
```

### Health Check

Check Graphiti status via the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Response includes Graphiti status:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "graphiti": true
  }
}
```

## Troubleshooting

### Graphiti Not Initializing

**Symptom:** Logs show "Graphiti initialization failed"

**Solutions:**
1. Check Neo4j is running: `docker ps | grep neo4j`
2. Verify Neo4j credentials in `.env`
3. Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j -p your_password`
4. Check OpenRouter API key is valid

### High Memory Usage

**Symptom:** Neo4j consuming too much memory

**Solutions:**
1. Limit Neo4j memory in Docker:
   ```bash
   docker run -e NEO4J_server_memory_heap_max__size=512m neo4j:5.26
   ```
2. Configure episode retention policy
3. Periodically archive old data

### Slow Episode Recording

**Symptom:** Graphiti recording takes >1 second

**Solutions:**
1. Use faster LLM model: `gpt-3.5-turbo` or `gemini-pro`
2. Reduce episode text length (already limited to top 10 campaigns)
3. Check Neo4j performance and indexes

### System Works Without Graphiti

**This is expected!** Graphiti is optional. If initialization fails:
- System logs a warning
- Continues normal operation
- All retrieval functionality works
- No latency impact

## Cost Estimation

### OpenRouter Costs

Assuming 1,000 queries/day:

| Model | Cost per Query | Monthly Cost |
|-------|---------------|--------------|
| `gpt-3.5-turbo` | $0.0001 | $3 |
| `gemini-pro` | $0.0002 | $6 |
| `claude-3.5-sonnet` | $0.0005 | $15 |
| `gpt-4` | $0.001 | $30 |

### Neo4j Costs

- **Local/Docker**: Free
- **Neo4j Aura Free**: Free (up to 50k nodes)
- **Neo4j Aura Pro**: $65/month (starts at)

## Best Practices

### 1. Start Disabled

Deploy with `GRAPHITI_ENABLED=false` initially, then enable gradually:

```bash
# Week 1: Disabled, monitor baseline
GRAPHITI_ENABLED=false

# Week 2: Enable for 10% of traffic
GRAPHITI_ENABLED=true  # Add traffic routing logic

# Week 3: Enable for 100%
GRAPHITI_ENABLED=true
```

### 2. Monitor Recording Success Rate

Track Graphiti recording success rate:

```python
# Add metrics tracking
graphiti_success_rate = successful_recordings / total_queries
assert graphiti_success_rate > 0.95  # Target: >95%
```

### 3. Implement Retention Policy

Archive or delete old episodes periodically:

```cypher
// Delete episodes older than 90 days
MATCH (e:Episode)
WHERE e.timestamp < datetime() - duration('P90D')
DELETE e
```

### 4. Use Appropriate LLM Model

- **Development**: `gpt-3.5-turbo` (fast, cheap)
- **Production**: `claude-3.5-sonnet` (balanced)
- **High-quality**: `gpt-4` (expensive, best quality)

## Future Enhancements

### Phase 2: Pre-Computed Graph Features

Query Graphiti nightly for campaign relationships, cache results for fast lookup during ranking:

```python
# Nightly job
async def update_campaign_features():
    for campaign in campaigns:
        related = await graphiti.get_related_campaigns(campaign.id)
        cache.set(f"related:{campaign.id}", related)

# During ranking (1ms lookup)
related_campaigns = cache.get(f"related:{campaign.id}")
```

### Phase 3: Personalized Ranking

Use user journey patterns to adjust ranking:

```python
# Get user's historical preferences
user_history = await graphiti.get_user_journey(user_id)
preferred_categories = extract_preferences(user_history)

# Boost campaigns in preferred categories
for campaign in campaigns:
    if campaign.category in preferred_categories:
        campaign.score *= 1.2
```

### Phase 4: Query Prediction

Predict likely next queries and pre-warm cache:

```python
# Predict next queries based on current query
next_queries = await graphiti.predict_next_queries(current_query)

# Pre-compute embeddings and cache results
for query in next_queries:
    asyncio.create_task(cache.warm(query))
```

## Support

For issues or questions:
1. Check logs for Graphiti warnings
2. Verify Neo4j is running and accessible
3. Test OpenRouter API key
4. Review this documentation
5. Check Graphiti docs: https://help.getzep.com/graphiti

## References

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [OpenRouter](https://openrouter.ai/)
- [Neo4j Documentation](https://neo4j.com/docs/)

---
name: Graphiti Phase 1 Integration
overview: Implement zero-latency Graphiti knowledge graph integration for async learning and enrichment of user queries, clicks, and campaign interactions without impacting the current 24ms retrieval latency.
todos:
  - id: install-deps
    content: Install graphiti-core and neo4j dependencies
    status: pending
  - id: config-updates
    content: Add Graphiti configuration to Settings and .env
    status: pending
  - id: graphiti-repository
    content: Create GraphitiRepository for Neo4j connection and episode management
    status: pending
  - id: graphiti-service
    content: Create GraphitiService for async event recording
    status: pending
  - id: event-models
    content: Create event models for structured Graphiti episodes
    status: pending
  - id: controller-integration
    content: Update RetrievalController with fire-and-forget Graphiti recording
    status: pending
  - id: dependency-injection
    content: Update dependencies.py to initialize Graphiti with graceful degradation
    status: pending
  - id: analytics-endpoints
    content: Create optional analytics endpoints for querying knowledge graph
    status: pending
  - id: integration-tests
    content: Write integration tests for Graphiti recording and error handling
    status: pending
  - id: benchmark-validation
    content: Run benchmarks to confirm zero latency impact
    status: pending
  - id: documentation
    content: Update README and create Graphiti integration documentation
    status: pending
isProject: false
---

# Phase 1: Zero-Latency Graphiti Integration

## Architecture Overview

This implementation adds Graphiti as an **async learning layer** that records user interactions and builds a temporal knowledge graph without affecting retrieval latency. All Graphiti operations happen **after** the response is returned to the user.

```mermaid
flowchart TD
    UserQuery[User Query] --> RetrievalController
    RetrievalController --> FastPipeline[Fast Pipeline 24ms]
    FastPipeline --> Response[Return Response]
    Response --> User[User receives response]
    
    Response -.->|Fire and forget| GraphitiService[Graphiti Service]
    GraphitiService --> RecordQuery[Record Query Event]
    GraphitiService --> BuildGraph[Build Knowledge Graph]
    BuildGraph --> Neo4j[(Neo4j/FalkorDB)]
    
    style Response fill:#90EE90
    style GraphitiService fill:#87CEEB
    style FastPipeline fill:#90EE90
```



## Implementation Steps

### 1. Install Dependencies

Add to `[requirements.txt](requirements.txt)`:

```txt
# Knowledge Graph
graphiti-core==0.28.1
neo4j==5.26.0
```

### 2. Configuration Updates

Add Graphiti settings to `[src/core/config.py](src/core/config.py)`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Graphiti settings
    GRAPHITI_ENABLED: bool = True
    GRAPHITI_NEO4J_URI: str = "bolt://localhost:7687"
    GRAPHITI_NEO4J_USER: str = "neo4j"
    GRAPHITI_NEO4J_PASSWORD: str = "password"
    OPENROUTER_API_KEY: str = ""  # For Graphiti's entity extraction via OpenRouter
    GRAPHITI_LLM_MODEL: str = "anthropic/claude-3.5-sonnet"  # OpenRouter model
    GRAPHITI_NAMESPACE: str = "ad_retrieval"
```

Add to `[.env](.env)`:

```env
GRAPHITI_ENABLED=true
GRAPHITI_NEO4J_URI=bolt://localhost:7687
GRAPHITI_NEO4J_USER=neo4j
GRAPHITI_NEO4J_PASSWORD=your_password
OPENROUTER_API_KEY=your_openrouter_key
GRAPHITI_LLM_MODEL=anthropic/claude-3.5-sonnet
GRAPHITI_NAMESPACE=ad_retrieval
```

### 3. Create Graphiti Service

Create new file `src/services/graphiti_service.py`:

**Key Features:**

- Async event recording (fire-and-forget pattern)
- Records query events with context
- Tracks campaign impressions
- Builds temporal knowledge graph
- No impact on retrieval latency

**Event Types to Record:**

1. **Query Events**: User query + context + eligibility + categories
2. **Campaign Impressions**: Which campaigns were shown
3. **User Journey**: Sequential queries from same user/session

**Implementation Pattern:**

```python
class GraphitiService:
    async def record_query_event(
        self, 
        query: str, 
        context: dict, 
        eligibility: float,
        categories: list,
        campaigns: list
    ):
        # Build episode text describing the event
        episode = self._build_episode(query, context, eligibility, categories, campaigns)
        
        # Add to Graphiti (async, non-blocking)
        await self.graphiti_client.add_episode(
            name=f"query_{timestamp}",
            episode_body=episode,
            source_description="Ad Retrieval Query"
        )
```

### 4. Create Graphiti Repository

Create new file `src/repositories/graphiti_repository.py`:

**Responsibilities:**

- Initialize Graphiti client with OpenRouter LLM configuration
- Manage Neo4j connection
- Handle episode creation
- Provide query interface for analytics

**Key Methods:**

- `initialize()`: Setup Graphiti client with OpenRouter LLM and Neo4j connection
- `add_episode()`: Record event to knowledge graph
- `get_user_journey()`: Retrieve user's query history (for future use)
- `get_campaign_relationships()`: Query campaign co-occurrence patterns
- `shutdown()`: Cleanup connections

**OpenRouter Configuration:**

Graphiti supports custom LLM providers. Configure it to use OpenRouter by setting the base URL and API key:

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client import OpenAIClient

# Configure OpenRouter as LLM provider
llm_client = OpenAIClient(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
    model=llm_model  # e.g., "anthropic/claude-3.5-sonnet"
)

graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password, llm_client=llm_client)
```

### 5. Update Retrieval Controller

Modify `[src/controllers/retrieval_controller.py](src/controllers/retrieval_controller.py)`:

**Changes:**

- Inject `GraphitiService` as optional dependency
- After building response (line 172), fire async task to record event
- Use `asyncio.create_task()` for fire-and-forget pattern
- Wrap in try-except to prevent Graphiti errors from affecting retrieval

**Code Location:** After line 172, before `return RetrievalResponse`:

```python
# Fire-and-forget: Record to Graphiti (no latency impact)
if self.graphiti_service:
    asyncio.create_task(
        self._record_to_graphiti_safe(request, eligibility, categories, campaign_models)
    )

return RetrievalResponse(...)
```

Add helper method:

```python
async def _record_to_graphiti_safe(self, request, eligibility, categories, campaigns):
    try:
        await self.graphiti_service.record_query_event(
            query=request.query,
            context=context_dict,
            eligibility=eligibility,
            categories=categories,
            campaigns=campaigns[:10]  # Only record top 10 to reduce payload
        )
    except Exception as e:
        logger.warning(f"Graphiti recording failed (non-critical): {e}")
```

### 6. Update Dependency Injection

Modify `[src/core/dependencies.py](src/core/dependencies.py)`:

**Changes:**

- Add global `_graphiti_repo` variable
- Initialize `GraphitiRepository` in `init_dependencies()` (with try-except for optional setup)
- Add `GraphitiService` to controller initialization
- Handle graceful degradation if Graphiti is disabled or fails

**Pattern:**

```python
# Initialize Graphiti (optional - graceful degradation)
if settings.GRAPHITI_ENABLED:
    try:
        _graphiti_repo = GraphitiRepository(
            neo4j_uri=settings.GRAPHITI_NEO4J_URI,
            neo4j_user=settings.GRAPHITI_NEO4J_USER,
            neo4j_password=settings.GRAPHITI_NEO4J_PASSWORD,
            openrouter_api_key=settings.OPENROUTER_API_KEY,
            llm_model=settings.GRAPHITI_LLM_MODEL
        )
        await _graphiti_repo.initialize()
        logger.info("✓ Graphiti repository initialized (using OpenRouter)")
    except Exception as e:
        logger.warning(f"Graphiti initialization failed (optional): {e}")
        _graphiti_repo = None
```

### 7. Create Event Models

Create new file `src/api/models/events.py`:

**Purpose:** Define structured event models for Graphiti

**Models:**

- `QueryEvent`: Query + context + results metadata
- `CampaignImpression`: Campaign shown to user
- `UserSession`: Track session-level patterns

### 8. Add Analytics Endpoint (Optional)

Create new file `src/api/routes/analytics.py`:

**Endpoints:**

- `GET /api/analytics/user-journey`: Retrieve user's query history
- `GET /api/analytics/campaign-relationships`: Get campaign co-occurrence data
- `GET /api/analytics/popular-categories`: Category trends over time

**Note:** These are read-only analytics endpoints with no latency constraints.

### 9. Testing Strategy

Create `tests/integration/test_graphiti_integration.py`:

**Test Cases:**

1. **Test async recording**: Verify events are recorded without blocking
2. **Test graceful degradation**: System works when Graphiti is disabled
3. **Test error handling**: Graphiti failures don't affect retrieval
4. **Test latency impact**: Confirm retrieval latency unchanged
5. **Test event structure**: Verify episode format is correct

**Benchmark Test:**

- Run benchmark before and after Graphiti integration
- Confirm P95 latency remains under 30ms
- Verify no increase in error rate

### 10. Documentation

Update `[README.md](README.md)`:

**Sections to add:**

- Graphiti integration overview
- Setup instructions for Neo4j
- Configuration options
- Analytics capabilities
- Future enhancement roadmap

Create `docs/GRAPHITI_INTEGRATION.md`:

**Contents:**

- Architecture diagram
- Event schema documentation
- Query examples for analytics
- Troubleshooting guide

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Controller
    participant Pipeline
    participant GraphitiService
    participant Neo4j
    
    User->>API: POST /api/retrieve
    API->>Controller: retrieve(request)
    Controller->>Pipeline: Execute fast pipeline
    Pipeline-->>Controller: Response (24ms)
    Controller-->>API: Return response
    API-->>User: 200 OK (24ms)
    
    Note over Controller,GraphitiService: Async - happens after response
    Controller--)GraphitiService: create_task(record_event)
    GraphitiService--)Neo4j: Add episode (async)
    Neo4j--)GraphitiService: Acknowledged
```



## Key Design Decisions

### Fire-and-Forget Pattern

Use `asyncio.create_task()` to record events asynchronously after response is sent. This ensures **zero latency impact** on retrieval.

### Graceful Degradation

If Graphiti is disabled or fails, the system continues to work normally. Graphiti is treated as an **optional enhancement**, not a critical dependency.

### Minimal Payload

Only record top 10 campaigns (not all 1000) to reduce Graphiti processing time and storage.

### Error Isolation

Wrap all Graphiti calls in try-except blocks. Log warnings but never propagate errors to the retrieval pipeline.

### Neo4j vs FalkorDB

Start with Neo4j (more mature, better docs). Can switch to FalkorDB later for better performance if needed.

### OpenRouter for LLM Calls

Use OpenRouter instead of OpenAI directly for Graphiti's entity extraction and relationship building. Benefits:

- Access to multiple models (Claude, GPT-4, Llama, etc.)
- Unified API and billing
- Cost optimization by choosing appropriate models
- Fallback options if one provider is down

Graphiti uses the OpenAI-compatible API, so OpenRouter works seamlessly by setting the base URL to `https://openrouter.ai/api/v1`.

## Success Metrics

1. **Zero Latency Impact**: P95 latency remains ≤30ms after integration
2. **Event Recording Rate**: >95% of queries successfully recorded
3. **System Stability**: No increase in error rate or crashes
4. **Knowledge Graph Growth**: Graph builds over time with meaningful relationships

## Future Enhancements (Phase 2+)

Once Phase 1 is stable, these become possible:

1. **Pre-computed Graph Features**: Nightly job queries Graphiti for campaign relationships, caches results
2. **User Journey Prediction**: Use graph patterns to predict next query
3. **Personalized Ranking**: Adjust ranking based on user's historical patterns
4. **A/B Testing Framework**: Track which ranking strategies work best
5. **Real-time Recommendations**: Separate endpoint with 200ms budget using live graph queries

## Rollout Plan

1. **Development**: Implement on local with Docker Neo4j
2. **Testing**: Run integration tests + benchmark validation
3. **Staging**: Deploy with `GRAPHITI_ENABLED=false` initially
4. **Gradual Rollout**: Enable for 10% → 50% → 100% of traffic
5. **Monitor**: Track latency, error rates, graph growth
6. **Optimize**: Tune episode format, batch recording if needed


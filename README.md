# Ad Retrieval System

A high-performance ad retrieval API that classifies commercial intent, extracts categories, and returns relevant campaigns within a **100ms latency budget**.

## Overview

This system processes user queries with optional context to:
1. Classify commercial intent (ad eligibility score 0.0-1.0)
2. Extract relevant product/service categories
3. Search and rank campaigns by relevancy
4. Return top 1,000 candidates

**Target Latency:** < 100ms (p95)

## Architecture

### System Architecture Diagram

![Architecture Diagram](assets/architecture-diagram.png)

### RCSR Pattern

The system follows the **Routes-Controllers-Services-Repositories** architecture:

- **Routes** (`src/api/routes/`): HTTP endpoint definitions
- **Controllers** (`src/controllers/`): Orchestrate service calls and business flow
- **Services** (`src/services/`): Business logic (eligibility, categories, embedding, search, ranking)
- **Repositories** (`src/repositories/`): Data access (FAISS, campaigns, blocklist, taxonomy)

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI + Uvicorn | High-performance async HTTP server |
| Validation | Pydantic | Request/response schema validation |
| Async Orchestration | asyncio | Parallel execution of independent tasks |
| Eligibility Scoring | Python regex + set lookups | Fast rule-based classification |
| Category Extraction | scikit-learn TfidfVectorizer | Keyword matching against taxonomy |
| Embeddings | sentence-transformers | Local model inference (all-MiniLM-L6-v2) |
| Vector Search | FAISS IndexFlatL2 | In-memory similarity search |
| Ranking | NumPy + Python | Score computation and sorting |
| Data Generation | Faker | Synthetic campaign creation |

## Project Structure

```
gravity/
├── src/
│   ├── api/              # API layer
│   │   ├── main.py       # FastAPI app
│   │   ├── routes/       # Endpoint definitions
│   │   └── models/       # Request/response DTOs
│   ├── controllers/      # Orchestration layer
│   ├── services/         # Business logic
│   ├── repositories/     # Data access
│   ├── core/             # Configuration
│   └── utils/            # Utilities
├── data/                 # Data files
│   ├── campaigns.jsonl   # 10k+ campaigns (generated)
│   ├── embeddings.npy    # Pre-computed embeddings (generated)
│   ├── faiss.index       # FAISS index (generated)
│   ├── blocklist.txt     # Safety blocklist
│   └── taxonomy.json     # Category taxonomy
├── scripts/              # Data generation and utilities
├── tests/                # Unit and integration tests
└── requirements.txt      # Python dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gravity
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate synthetic campaign data:
```bash
python scripts/generate_data.py
```

This will create `data/campaigns.jsonl` with 10,000 synthetic campaigns.

5. Build the FAISS index (coming in Phase 5):
```bash
python scripts/build_index.py
```

## Configuration

Environment variables can be set in `.env`:

```env
HOST=0.0.0.0
PORT=8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_CANDIDATES=1500
MAX_CAMPAIGNS_RETURNED=1000
```

## Quick Start

### 1. Start the Server

```bash
python -m uvicorn src.api.main:app --reload
```

Server will start at `http://localhost:8000`

### 2. Test the API

Visit the interactive docs: **http://localhost:8000/docs**

Or run the test script:
```bash
python test_api.py
```

Or use cURL:
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "running shoes for marathon"}'
```

### 3. Run Benchmarks

```bash
python scripts/benchmark.py --runs 100
```

## API Usage

### Endpoint

```
POST /api/retrieve
```

### Example 1: Commercial Query with Context

**Request:**
```json
{
  "query": "Best running shoes for marathon training",
  "context": {
    "age": 30,
    "gender": "male",
    "location": "San Francisco, CA",
    "interests": ["fitness", "running", "health"]
  }
}
```

**Response:**
```json
{
  "ad_eligibility": 0.95,
  "extracted_categories": ["running_shoes", "marathon_gear", "athletic_footwear"],
  "campaigns": [
    {
      "campaign_id": "camp_00123",
      "relevance_score": 1.0,
      "title": "Nike Premium Marathon Trainers",
      "category": "running_shoes",
      "description": "Professional marathon training shoes",
      "keywords": ["running", "marathon", "training"]
    }
  ],
  "latency_ms": 58.23,
  "metadata": {
    "candidates_retrieved": 1500,
    "campaigns_returned": 1000,
    "top_relevance_score": 1.0
  }
}
```

### Example 2: Blocked Query (Short-Circuit)

**Request:**
```json
{
  "query": "I want to commit suicide"
}
```

**Response:**
```json
{
  "ad_eligibility": 0.0,
  "extracted_categories": ["general"],
  "campaigns": [],
  "latency_ms": 13.29,
  "metadata": {
    "short_circuited": true,
    "reason": "Zero eligibility score"
  }
}
```

### Example 3: Informational Query

**Request:**
```json
{
  "query": "What is the history of marathon running?"
}
```

**Response:**
```json
{
  "ad_eligibility": 0.75,
  "extracted_categories": ["marathon_gear", "running_shoes"],
  "campaigns": [...],
  "latency_ms": 62.15,
  "metadata": {
    "candidates_retrieved": 1500,
    "campaigns_returned": 1000
  }
}
```

## Development Status

### ✅ Phase 1: Project Setup & Synthetic Data
- [x] RCSR project structure
- [x] Configuration and dependencies
- [x] Category taxonomy (45 categories)
- [x] Safety blocklist
- [x] Synthetic data generator (10k campaigns)

### ✅ Phase 2: API Models & Middleware
- [x] FastAPI application setup
- [x] Request/response Pydantic models
- [x] CORS middleware
- [x] Latency tracking middleware
- [x] Global exception handler

### ✅ Phase 3: Eligibility Service
- [x] BlocklistRepository with safety rules
- [x] EligibilityService with commercial intent scoring
- [x] Integration tests (14 tests passing)

### ✅ Phase 4: Category Extraction
- [x] TaxonomyRepository
- [x] CategoryService with TF-IDF matching
- [x] Integration tests (19 tests passing)

### ✅ Phase 5: Embedding & Search
- [x] EmbeddingService (sentence-transformers)
- [x] VectorRepository (FAISS)
- [x] CampaignRepository
- [x] SearchService
- [x] Integration tests (33 tests passing)

### ✅ Phase 6: Ranking Service
- [x] RankingService with multi-signal ranking
- [x] Category matching boosts
- [x] Context-based targeting
- [x] Integration tests (20 tests passing)

### ✅ Phase 7: Controller & Orchestration
- [x] RetrievalController with async pipeline
- [x] Dependency injection
- [x] Parallel processing optimization
- [x] Integration tests (16 tests passing)

### ✅ Phase 8: Testing & Benchmarking
- [x] Test query suite (12 diverse scenarios)
- [x] Benchmark script with P95/P99 metrics
- [x] API test script
- [x] 102 integration tests passing

### ✅ Phase 9: Documentation
- [x] README with architecture
- [x] TESTING.md guide
- [x] API documentation (Swagger/ReDoc)
- [x] Design decisions documented

**Status: Production Ready** 🎉

## Design Decisions

### Local Models vs. API Calls
**Decision:** Use local sentence-transformers model  
**Rationale:** API calls add 50-200ms latency. Local inference with `all-MiniLM-L6-v2` is ~5ms.  
**Trade-off:** Lower embedding quality vs. meeting latency budget.

### FAISS vs. Vector Databases
**Decision:** FAISS in-memory index  
**Rationale:** For 10k vectors, FAISS is <10ms. Cloud vector DBs add network overhead (20-50ms).  
**Trade-off:** No persistence/scalability features vs. raw speed.

### Rule-based Eligibility vs. LLM
**Decision:** Rule-based classifier with blocklist  
**Rationale:** LLM calls are 100-500ms. Rules achieve <10ms.  
**Trade-off:** Less nuanced scoring vs. meeting latency budget.

## Performance Results

### Actual Latency (Measured)

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| **End-to-End Pipeline** | <100ms | **23.91ms avg** | ✅ 76% faster |
| **P95 Latency** | <100ms | **25.88ms** | ✅ 74% faster |
| **P99 Latency** | <100ms | **~27ms** | ✅ 73% faster |
| Short-Circuit (blocked) | N/A | **13.61ms** | ✅ Ultra-fast |
| Query Embedding | <10ms | **6.62ms** | ✅ 34% faster |
| Vector Search | <15ms | **1.77ms** | ✅ 88% faster |
| Ranking (1000 campaigns) | <20ms | **1.08ms** | ✅ 94.6% faster |

### Latency Breakdown

| Component | Target | Actual | Strategy |
|-----------|--------|--------|----------|
| Input validation | <1ms | <1ms | Pydantic models |
| Ad eligibility | 5-10ms | ~8ms | Rule-based + blocklist (offloaded to thread pool) |
| Category extraction | 5-10ms | ~5ms | TF-IDF + keyword matching (offloaded to thread pool) |
| Query embedding | 5-10ms | **6.62ms** | Local sentence-transformer (offloaded to thread pool) |
| Vector search | 10-15ms | **1.77ms** | In-memory FAISS (offloaded to thread pool) |
| Relevance ranking | 10-20ms | **1.08ms** | NumPy operations |
| Response serialization | <5ms | <1ms | FastAPI JSON encoder |
| **Total server-side** | **50-70ms** | **~24ms** | 🎯 Target exceeded! |

### Latency Optimization

To meet the **< 100ms p95** latency requirement under concurrent load, all CPU-bound operations are offloaded to thread pools using `asyncio.to_thread()`:

1. **Embedding** (`EmbeddingService.embed_query`): SentenceTransformer model inference (~5-10ms)
2. **FAISS Search** (`VectorRepository.search`): k-NN search over 10k vectors (~2-5ms)
3. **Campaign Fetch** (`CampaignRepository.get_by_indices`): Dictionary lookups (~1-2ms)
4. **Eligibility Scoring** (`EligibilityService.score`): Regex pattern matching (~5-10ms)
5. **Category Extraction** (`CategoryService.extract`): TF-IDF vectorization (~3-5ms)

**Why this matters:** Without thread offloading, these synchronous operations block the asyncio event loop, preventing concurrent requests from making progress. Under load, this causes latency to spike from ~25ms to 200-400ms. With thread offloading, the event loop remains responsive and can handle 100+ concurrent requests while maintaining p95 < 100ms.

**Architecture:**
```
Event Loop (non-blocking)          Thread Pool (blocking work)
├─ Input validation                ├─ Eligibility regex
├─ Orchestration logic              ├─ Category TF-IDF
├─ Response serialization           ├─ Embedding model.encode()
└─ Async coordination               ├─ FAISS index.search()
                                    └─ Campaign dictionary lookups
```

### Test Coverage

- **102 integration tests** - All passing ✅
- **12 test query scenarios** - Commercial, informational, blocked
- **Performance benchmarks** - P95, P99, mean, median
- **Concurrent request handling** - Tested and validated

## Deployment

### Production Considerations

**Server Configuration:**
```bash
# Use gunicorn with uvicorn workers
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**Resource Requirements:**
- **Memory**: ~1-2GB (includes FAISS index, embeddings, models)
- **CPU**: 2+ cores recommended
- **Disk**: ~100MB for data files

**Environment Variables:**
```env
HOST=0.0.0.0
PORT=8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_CANDIDATES=1500
MAX_CAMPAIGNS_RETURNED=1000
```

**Health Checks:**
- Health: `GET /api/health`
- Readiness: `GET /api/ready`

**Monitoring:**
- All responses include `X-Latency-Ms` header
- Slow requests (>100ms) are logged automatically
- Detailed logging with request IDs

### Deployment Platforms

**Railway / Render / Fly.io:**
1. Set Python version to 3.11+
2. Install command: `pip install -r requirements.txt`
3. Start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
4. Ensure data files are included in deployment

**Docker:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing guide.

**Quick Test:**
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run benchmark
python scripts/benchmark.py --runs 100

# Test API interactively
python test_api.py
```

## License

MIT

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

## API Usage

### Endpoint

```
POST /api/retrieve
```

### Request

```json
{
  "query": "I'm running a marathon next month and need new shoes",
  "context": {
    "gender": "male",
    "age": 24,
    "location": "San Francisco, CA",
    "interests": ["fitness", "outdoor activities"]
  }
}
```

### Response

```json
{
  "ad_eligibility": 0.95,
  "extracted_categories": ["running_shoes", "marathon_gear", "athletic_footwear"],
  "campaigns": [
    {
      "campaign_id": "camp_00123",
      "relevance_score": 0.94,
      "title": "Nike Premium Running Shoes",
      "category": "running_shoes",
      "description": "...",
      "keywords": ["running", "marathon", "athletic"]
    }
  ],
  "latency_ms": 67,
  "metadata": {
    "candidates_retrieved": 1500,
    "campaigns_returned": 1000
  }
}
```

## Development Status

### Phase 1: Project Setup & Synthetic Data ✅
- [x] RCSR project structure
- [x] Configuration and dependencies
- [x] Category taxonomy (50+ categories)
- [x] Safety blocklist
- [x] Synthetic data generator (10k campaigns)

### Phase 2-9: Coming Soon
- [ ] Core API implementation
- [ ] Eligibility scoring service
- [ ] Category extraction service
- [ ] Embedding and vector search
- [ ] Relevance ranking
- [ ] Controller orchestration
- [ ] Testing and benchmarking
- [ ] Deployment

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

## Latency Budget

| Component | Target | Strategy |
|-----------|--------|----------|
| Network overhead | ~10-20ms | (uncontrollable) |
| Input validation | <1ms | Pydantic models |
| Ad eligibility | 5-10ms | Rule-based + blocklist |
| Category extraction | 5-10ms | TF-IDF + keyword matching |
| Query embedding | 5-10ms | Local sentence-transformer |
| Vector search | 10-15ms | In-memory FAISS |
| Relevance ranking | 10-20ms | NumPy operations |
| Response serialization | <5ms | FastAPI JSON encoder |
| **Total server-side** | **50-70ms** | Leaves 20-30ms buffer |

## License

MIT

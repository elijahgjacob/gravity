# Test Organization

Tests are organized by development phase according to the Technical Development Plan (TDP).

## Phase-Based Test Structure

### Phase 1: Project Setup & Synthetic Data ✅
**Location:** `tests/phase1/`

Tests for foundational components:
- `test_config.py` - Configuration settings and environment variables
- `test_data_generation.py` - Synthetic campaign generation (10k+ campaigns)
- `test_taxonomy.py` - Category taxonomy structure (50+ categories)
- `test_blocklist.py` - Safety blocklist validation

**Status:** 34 tests passing

### Phase 2: Core API & RCSR Setup
**Location:** `tests/phase2/`

Tests for API layer:
- FastAPI application initialization
- Request/response Pydantic models
- Route definitions
- Middleware (CORS, latency tracking)

**Status:** Not yet implemented

### Phase 3: Services Layer - Eligibility
**Location:** `tests/phase3/`

Tests for ad eligibility scoring:
- Eligibility service business logic
- Blocklist repository data access
- Safety filtering (0.0 scores)
- Commercial intent detection (0.8-1.0 scores)
- Sensitive content handling (0.4-0.7 scores)

**Status:** Not yet implemented

### Phase 4: Services Layer - Categories
**Location:** `tests/phase4/`

Tests for category extraction:
- Category service business logic
- Taxonomy repository data access
- TF-IDF keyword matching
- Context-based category boosting
- 1-10 category enforcement

**Status:** Not yet implemented

### Phase 5: Services Layer - Embedding & Search
**Location:** `tests/phase5/`

Tests for vector search:
- Embedding service (sentence-transformers)
- Search service business logic
- Vector repository (FAISS index)
- Campaign repository data access
- Query embedding generation
- Top-k similarity search

**Status:** Not yet implemented

### Phase 6: Services Layer - Ranking
**Location:** `tests/phase6/`

Tests for relevance ranking:
- Ranking service business logic
- Category matching boosts
- Context-based targeting boosts (age, gender, location, interests)
- Score normalization (0.0-1.0)

**Status:** Not yet implemented

### Phase 7: Controller Layer - Orchestration
**Location:** `tests/phase7/`

Tests for request orchestration:
- Retrieval controller flow
- Dependency injection
- Async parallel execution (eligibility + categories)
- Short-circuit logic (eligibility = 0.0)
- Pipeline integration

**Status:** Not yet implemented

### Phase 8: Testing & Benchmarking
**Location:** `tests/phase8/`

Integration and performance tests:
- End-to-end API tests
- Latency benchmarks (<100ms p95)
- Test query validation
- Edge case scenarios
- Load testing

**Status:** Not yet implemented

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run tests for a specific phase
```bash
pytest tests/phase1/ -v
pytest tests/phase2/ -v
# etc.
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/phase1/test_config.py -v
```

## Test Conventions

1. **Naming:** Test files follow `test_<module>.py` pattern
2. **Functions:** Test functions follow `test_<feature>` pattern
3. **Assertions:** Use descriptive assertion messages
4. **Fixtures:** Share fixtures via `conftest.py` in each phase directory
5. **Mocking:** Mock external dependencies (models, databases) in unit tests
6. **Integration:** Phase 8 contains integration tests that test multiple components together

## Coverage Goals

- **Unit Tests:** 80%+ coverage for services, repositories, controllers
- **Integration Tests:** Cover all API endpoints and critical paths
- **Performance Tests:** Validate <100ms p95 latency requirement

## Current Status

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 1 | 34 | ✅ Passing |
| Phase 2 | 0 | ⏳ Pending |
| Phase 3 | 0 | ⏳ Pending |
| Phase 4 | 0 | ⏳ Pending |
| Phase 5 | 0 | ⏳ Pending |
| Phase 6 | 0 | ⏳ Pending |
| Phase 7 | 0 | ⏳ Pending |
| Phase 8 | 0 | ⏳ Pending |

**Total:** 34 tests passing

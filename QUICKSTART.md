# Quick Start Guide

## Phase 1 & 2 Complete - API Ready to Test

### Prerequisites

```bash
cd /Users/elijahgjacob/gravity
source venv/bin/activate
```

## 1. Validate Setup

### Phase 1 Validation
```bash
python scripts/validate_phase1.py
```

Expected output:
- ✅ 8/8 files exist
- ✅ 10,000 campaigns generated
- ✅ 45 categories in taxonomy
- ✅ 66 safety terms in blocklist
- ✅ 34/34 tests passing

### Phase 2 Validation
```bash
python scripts/validate_phase2.py
```

Expected output:
- ✅ 10/10 files exist
- ✅ 8/8 modules import
- ✅ 4 routes configured
- ✅ 25/25 tests passing

## 2. Run Tests

### All Tests
```bash
pytest tests/ -v
```

Expected: **59 tests passing** (34 Phase 1 + 25 Phase 2)

### Phase-Specific Tests
```bash
# Phase 1 only
pytest tests/phase1/ -v

# Phase 2 only
pytest tests/phase2/ -v
```

## 3. Start API Server

### Terminal 1: Start Server
```bash
cd /Users/elijahgjacob/gravity
source venv/bin/activate
uvicorn src.api.main:app --reload
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Server will be available at: **http://localhost:8000**

### Terminal 2: Test API

```bash
cd /Users/elijahgjacob/gravity
source venv/bin/activate
python scripts/test_api_server.py
```

## 4. Explore API Documentation

With server running, open in browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 5. Manual API Testing

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Readiness Check
```bash
curl http://localhost:8000/api/ready
```

### Retrieve Ads (Main Endpoint)
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need running shoes for a marathon",
    "context": {
      "age": 25,
      "gender": "male",
      "location": "San Francisco, CA",
      "interests": ["fitness", "running"]
    }
  }'
```

Expected response:
```json
{
  "ad_eligibility": 0.75,
  "extracted_categories": ["general"],
  "campaigns": [],
  "latency_ms": 0.0,
  "metadata": {
    "status": "Phase 2 - API structure only",
    "note": "Controller implementation pending (Phase 7)"
  }
}
```

## 6. Check Response Headers

```bash
curl -i http://localhost:8000/api/health
```

Look for:
- `X-Latency-Ms`: Request processing time
- `access-control-allow-origin`: CORS header

## Project Status

### ✅ Completed Phases

**Phase 1: Project Setup & Synthetic Data**
- RCSR architecture
- 10,000 synthetic campaigns
- Category taxonomy (45 categories)
- Safety blocklist (66 terms)
- 34 tests passing

**Phase 2: Core API & RCSR Setup**
- FastAPI application
- Request/response models
- API routes (health, retrieve)
- Logging & timing utilities
- Dependency injection
- 25 tests passing

### ⏳ Pending Phases

- Phase 3: Eligibility Service
- Phase 4: Category Service
- Phase 5: Embedding & Search
- Phase 6: Ranking Service
- Phase 7: Controller Orchestration
- Phase 8: Testing & Benchmarking

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Import errors
```bash
# Make sure you're in the project root
cd /Users/elijahgjacob/gravity

# Activate virtual environment
source venv/bin/activate

# Verify Python path
python -c "import sys; print(sys.path)"
```

### Tests failing
```bash
# Clean pytest cache
rm -rf .pytest_cache

# Reinstall dependencies
pip install -r requirements.txt

# Run tests with verbose output
pytest tests/ -vv
```

## Next Steps

Ready to implement Phase 3 (Eligibility Service):
- Blocklist repository
- Eligibility scoring (0.0-1.0)
- Safety filtering
- Commercial intent detection

**Total Progress: 2/9 phases (22%)** 🚀

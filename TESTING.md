# Testing Guide - Ad Retrieval API

## 🚀 Quick Start

### 1. Start the Server

```bash
# Start the development server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or with custom port
python -m uvicorn src.api.main:app --reload --port 8080
```

The server will start at `http://localhost:8000`

### 2. Run the Test Script

```bash
# Run the comprehensive test script
python test_api.py
```

This will test:
- Health and readiness endpoints
- Commercial queries with context
- Blocked queries (short-circuit)
- Informational queries
- Product queries
- Multi-product queries

## 📋 Manual Testing Options

### Option 1: Using cURL

#### Health Check
```bash
curl http://localhost:8000/api/health
```

#### Readiness Check
```bash
curl http://localhost:8000/api/ready
```

#### Retrieve Ads (Simple Query)
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes for marathon"
  }'
```

#### Retrieve Ads (With Context)
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Best running shoes for marathon training",
    "context": {
      "age": 30,
      "gender": "male",
      "location": "San Francisco, CA",
      "interests": ["fitness", "running", "health"]
    }
  }'
```

#### Blocked Query (Short-Circuit Test)
```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want to commit suicide"
  }'
```

### Option 2: Using HTTPie (if installed)

```bash
# Install httpie
pip install httpie

# Simple query
http POST localhost:8000/api/retrieve query="laptop for programming"

# With context
http POST localhost:8000/api/retrieve \
  query="yoga mat" \
  context:='{"age": 35, "gender": "female", "interests": ["yoga", "wellness"]}'
```

### Option 3: Using Python Requests

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/api/retrieve",
    json={"query": "running shoes"}
)
print(response.json())

# With context
response = requests.post(
    "http://localhost:8000/api/retrieve",
    json={
        "query": "fitness tracker",
        "context": {
            "age": 28,
            "gender": "female",
            "interests": ["fitness", "health"]
        }
    }
)
print(response.json())
```

### Option 4: Interactive API Documentation

Visit these URLs in your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can:
- View all endpoints
- See request/response schemas
- Test endpoints directly in the browser
- View example requests and responses

## 🧪 Running Integration Tests

### Run All Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Phase Tests
```bash
# Phase 3: Eligibility
pytest tests/integration/test_phase3_integration.py -v

# Phase 4: Category Extraction
pytest tests/integration/test_phase4_integration.py -v

# Phase 5: Embedding & Search
pytest tests/integration/test_phase5_integration.py -v

# Phase 6: Ranking
pytest tests/integration/test_phase6_integration.py -v

# Phase 7: End-to-End Controller
pytest tests/integration/test_phase7_integration.py -v
```

### Run Tests with Output
```bash
pytest tests/integration/test_phase7_integration.py -v -s
```

### Run Performance Tests Only
```bash
pytest tests/integration/ -v -k "latency"
```

## 📊 Expected Results

### Successful Response Example

```json
{
  "ad_eligibility": 0.95,
  "extracted_categories": [
    "running_shoes",
    "marathon_gear",
    "athletic_footwear"
  ],
  "campaigns": [
    {
      "campaign_id": "camp_001",
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

### Short-Circuit Response (Blocked Query)

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

## 🎯 Performance Benchmarks

Expected latencies (actual results):

| Scenario | Target | Actual | Status |
|----------|--------|--------|--------|
| Full Pipeline | <100ms | ~24ms | ✅ |
| Short-Circuit | N/A | ~13ms | ✅ |
| Commercial Query | <100ms | ~60ms | ✅ |
| With Context | <100ms | ~60ms | ✅ |

## 🔍 Test Scenarios

### 1. Commercial Intent Queries
```json
{
  "query": "buy running shoes",
  "expected_eligibility": ">0.9",
  "expected_categories": ["running_shoes", "athletic_footwear"]
}
```

### 2. Informational Queries
```json
{
  "query": "What is marathon training?",
  "expected_eligibility": "0.7-0.85",
  "expected_categories": ["marathon_gear", "running_shoes"]
}
```

### 3. Blocked Queries
```json
{
  "query": "suicide help",
  "expected_eligibility": "0.0",
  "expected_campaigns": 0,
  "short_circuit": true
}
```

### 4. Context-Aware Queries
```json
{
  "query": "fitness equipment",
  "context": {
    "age": 25,
    "gender": "male",
    "interests": ["gym", "weightlifting"]
  },
  "expected": "Gym equipment ranked higher"
}
```

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port is already in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Or use a different port
python -m uvicorn src.api.main:app --reload --port 8080
```

### Dependencies Not Initialized
```bash
# Check data files exist
ls -la data/

# Required files:
# - blocklist.txt
# - taxonomy.json
# - campaigns.jsonl
# - faiss.index
```

### Slow Performance
```bash
# Check system resources
top

# Verify FAISS index size
ls -lh data/faiss.index

# Check campaign count
wc -l data/campaigns.jsonl
```

### Tests Failing
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest tests/integration/ -vv
```

## 📈 Load Testing

### Using Apache Bench (ab)
```bash
# Install apache bench
brew install httpd  # macOS

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 -T 'application/json' \
  -p query.json \
  http://localhost:8000/api/retrieve
```

### Using wrk
```bash
# Install wrk
brew install wrk  # macOS

# Load test for 30 seconds, 10 connections
wrk -t10 -c10 -d30s \
  -s post.lua \
  http://localhost:8000/api/retrieve
```

## 🎓 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run Tests**: `pytest tests/integration/ -v`
3. **Check Performance**: Run `test_api.py` multiple times
4. **Customize Queries**: Modify `test_api.py` with your own test cases
5. **Monitor Logs**: Watch the server output for detailed timing

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health
- **Readiness Check**: http://localhost:8000/api/ready

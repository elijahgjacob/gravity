# Performance Testing Results

## Overview

This document summarizes the performance characteristics of the Ad Retrieval API under various load conditions.

## Test Environments

### Local Testing
- **Hardware**: MacBook
- **Python**: 3.12
- **Server**: Uvicorn (single worker)
- **Dataset**: 10,000 campaigns, 384-dimensional embeddings
- **Network**: Local (localhost:8000)

### Railway Production Testing
- **Platform**: Railway (https://gravity-api-production.up.railway.app)
- **Instance**: Single replica
- **Network**: Public internet (tested via mobile hotspot)
- **Dataset**: Same (10,000 campaigns, 384-dimensional embeddings)

## Sequential Performance

**Benchmark**: 1,200 requests (100 runs × 12 test queries)

| Metric | Value | Status |
|--------|-------|--------|
| Mean | 25.99ms | ✅ |
| Median (P50) | 24.43ms | ✅ |
| P90 | 28.87ms | ✅ |
| **P95** | **36.73ms** | ✅ **Target: < 100ms** |
| P99 | 78.47ms | ✅ |
| Requests/sec | 27.92 | ✅ |

**Verdict**: Excellent performance for sequential requests.

## Concurrent Performance (Single Instance)

### Local Testing (localhost)

| Concurrency | Mean | P95 | Status |
|-------------|------|-----|--------|
| 1 concurrent | 64.79ms | 64.79ms | ✅ |
| 2 concurrent | 26.70ms | 27.85ms | ✅ |
| 3 concurrent | 43.06ms | 52.63ms | ✅ |
| 4 concurrent | 63.39ms | 78.00ms | ✅ |
| **5 concurrent** | **74.48ms** | **107.38ms** | ❌ **Threshold** |
| 10 concurrent | 152.88ms | 198.96ms | ❌ |
| 20 concurrent | 166.50ms | 257.29ms | ❌ |

### Railway Production Testing (Single Replica)

| Concurrency | Total Requests | Mean | P50 | P95 | Status |
|-------------|----------------|------|-----|-----|--------|
| 10 concurrent | 100 | 184.42ms | 175.62ms | **321.69ms** | ❌ |
| 25 concurrent | 250 | 381.83ms | 388.34ms | **739.10ms** | ❌ |
| 50 concurrent | 500 | 774.29ms | 800.14ms | **1328.10ms** | ❌ |
| 100 concurrent | 1000 | 812.48ms | 892.44ms | **1286.14ms** | ❌ |

**Key Findings**: 
- Railway shows slightly higher latency than local testing (network overhead)
- Single instance cannot meet <100ms P95 target under any concurrent load
- Minimum latency: 27ms (confirms fast sequential performance)
- **Horizontal scaling required for production concurrent load**

## Root Cause Analysis

### Why does latency degrade under concurrency?

Python's **Global Interpreter Lock (GIL)** prevents true parallelism for CPU-bound operations:

1. **Embedding** (`model.encode`): ~5-10ms of CPU-bound work
2. **FAISS search** (`index.search`): ~2-5ms of CPU-bound work
3. **TF-IDF** (`vectorizer.transform`): ~3-5ms of CPU-bound work
4. **Regex** (eligibility/category): ~5-10ms of CPU-bound work

Even though these operations are wrapped in `async` functions, they execute synchronously and hold the GIL. When multiple requests arrive concurrently, they queue up waiting for the GIL, causing latency to increase linearly with concurrency.

### Why doesn't `asyncio.to_thread()` help?

We tested offloading CPU-bound work to thread pools using `asyncio.to_thread()`. Results:

- **Sequential**: 25ms → 332ms (13x slower) ❌
- **10 concurrent**: 162ms → 557ms (3.4x slower) ❌

**Conclusion**: Thread offloading adds overhead without providing true parallelism due to the GIL. The threads still serialize execution.

## Solution: Horizontal Scaling

### Single Instance Limitations

A single Python process can efficiently handle:
- **Sequential requests**: ~28 requests/sec
- **Concurrent requests**: Up to 4 simultaneous requests with p95 < 100ms

### Multi-Instance Deployment

With **N instances**, the system can handle:
- **Concurrent requests**: N × 4 simultaneous requests
- **Throughput**: N × 28 requests/sec

**Example**: 3 instances
- Can handle 12 concurrent requests with p95 < 100ms
- Throughput: ~84 requests/sec
- Total capacity: ~5,000 requests/minute

### Railway Configuration

To configure multiple replicas on Railway:

1. Navigate to your service in the Railway dashboard
2. Go to **Settings** → **Replicas**
3. Set **Number of Replicas** to 2-4 (start with 2)
4. Railway's load balancer will automatically distribute traffic

**Cost consideration**: Each replica consumes resources. Start with 2 replicas and monitor:
- If p95 latency > 100ms: Add more replicas
- If CPU usage < 50%: May be over-provisioned

## Performance Targets

| Scenario | Target | Achieved | Method |
|----------|--------|----------|--------|
| Sequential requests | p95 < 100ms | **37ms** ✅ | Single instance |
| Light load (< 5 concurrent) | p95 < 100ms | **78ms** ✅ | Single instance |
| Medium load (5-20 concurrent) | p95 < 100ms | Requires 2-3 instances | Horizontal scaling |
| Heavy load (20+ concurrent) | p95 < 100ms | Requires 4+ instances | Horizontal scaling + auto-scaling |

## Recommendations

Based on testing both local and Railway deployments:

1. **Development/Testing**: Single instance is sufficient (sequential requests perform well)
2. **Production (any concurrent load)**: **Minimum 2 replicas required** to meet <100ms P95 target
3. **Production (10-25 concurrent)**: 2-3 replicas recommended
4. **Production (50+ concurrent)**: 4+ replicas with auto-scaling enabled
5. **Cost optimization**: Start with 2 replicas, monitor Railway metrics, scale up as needed

### Expected Performance with Horizontal Scaling

| Replicas | Max Concurrent (P95 < 100ms) | Throughput |
|----------|------------------------------|------------|
| 1 replica | ~4 requests | ~28 req/sec |
| 2 replicas | ~8-10 requests | ~56 req/sec |
| 3 replicas | ~12-15 requests | ~84 req/sec |
| 4 replicas | ~16-20 requests | ~112 req/sec |

## Test Scripts

- `scripts/benchmark.py`: Sequential performance testing
- `scripts/proper_stress_test.py`: Concurrent load testing
- `test_api.py`: Interactive API testing

## Conclusion

The application achieves **p95 < 37ms** for sequential requests and can maintain **p95 < 100ms** for up to 4 concurrent requests on a single instance. For higher concurrency, horizontal scaling (multiple Railway replicas) is the recommended approach, providing linear scalability without code changes.

# Railway Deployment Latency Guide

## 🔴 Problem: High Latency After Deployment

After deploying to Railway, you may experience significantly higher latency compared to local testing:

**Local Performance:**
- Mean: 23.8ms
- P95: 26.6ms
- P99: 50.9ms

**Railway Performance (Single Instance):**
- Sequential: ~30ms ✅
- 10 concurrent: 184ms avg, 321ms P95 ❌
- 25 concurrent: 381ms avg, 739ms P95 ❌
- 50+ concurrent: 774ms+ avg ❌

---

## 🎯 Root Causes

### 1. **Python GIL (Global Interpreter Lock)** - Primary Issue

**What is it?**
Python's GIL prevents true parallelism for CPU-bound operations. Even though the code uses `async/await`, CPU-intensive operations (embeddings, FAISS search, TF-IDF) hold the GIL and block other requests.

**Impact:**
```
Single Worker:
Request 1: [====25ms====] (using GIL)
Request 2:              [====waits====][====25ms====]
Request 3:                                          [====waits====][====25ms====]
Result: Linear latency increase with concurrent load
```

**What operations are affected?**
- Embedding generation: `model.encode()` → 5-10ms
- FAISS search: `index.search()` → 2-5ms
- TF-IDF vectorization: `vectorizer.transform()` → 3-5ms
- Regex matching: eligibility/category → 5-10ms

### 2. **Cold Starts**

**What is it?**
Railway may spin down idle services to save resources. When a request arrives after idle period:
- Container restart: 1-3 seconds
- Model loading: 5-10 seconds (first request)
- FAISS index loading: 1-2 seconds

**Impact:**
- First request: 5-15 seconds ❌
- Subsequent requests: Normal latency ✅

### 3. **Single Worker Configuration**

**Current Setup:**
```json
"startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
```
This runs a **single worker process** that can't handle concurrent requests efficiently.

---

## ✅ Solutions (Ranked by Effectiveness)

### **Solution 1: Enable Railway Replicas** (Recommended)

**Best for:** Production deployments, any concurrent load

Railway can run multiple instances with automatic load balancing:

#### Steps:
1. Go to Railway Dashboard
2. Select your service
3. Click **Settings** → **Replicas**
4. Set **Number of Replicas** to **2-3**
5. Save changes

#### Expected Results:

| Replicas | Max Concurrent | P95 Latency | Throughput |
|----------|----------------|-------------|------------|
| 1        | ~4 requests    | 78ms        | ~28 req/sec |
| 2        | ~8-10 requests | ~60ms       | ~56 req/sec |
| 3        | ~12-15 requests| ~50ms       | ~84 req/sec |
| 4        | ~16-20 requests| ~45ms       | ~112 req/sec |

#### Pros:
- ✅ No code changes required
- ✅ Railway handles load balancing automatically
- ✅ Easy to scale up/down based on traffic
- ✅ Each replica is a separate process (bypasses GIL)

#### Cons:
- ❌ Higher cost (each replica is billed separately)

#### Cost:
Each replica costs the same as your current instance. Start with 2 replicas and monitor metrics.

---

### **Solution 2: Use Gunicorn Multi-Worker** (Alternative)

**Best for:** Single-instance deployments, cost optimization

Run multiple worker processes within a single Railway instance:

#### Changes Made:

**1. Added gunicorn to requirements.txt:**
```python
gunicorn==21.2.0
```

**2. Updated railway.json:**
```json
{
  "deploy": {
    "startCommand": "gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120"
  }
}
```

#### Configuration Options:

```bash
# 2 workers (for small Railway instances)
gunicorn src.api.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

# 4 workers (for medium instances)
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

# Auto-detect workers (2 * CPU cores + 1)
gunicorn src.api.main:app --workers $(( $(nproc) * 2 + 1 )) --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

#### Expected Results:

| Workers | Max Concurrent | P95 Latency | Memory Usage |
|---------|----------------|-------------|--------------|
| 1       | ~4 requests    | 78ms        | ~1GB         |
| 2       | ~8 requests    | ~60ms       | ~2GB         |
| 4       | ~16 requests   | ~50ms       | ~4GB         |

#### Pros:
- ✅ Single Railway instance (lower cost)
- ✅ Each worker is a separate process (bypasses GIL)
- ✅ Handles concurrent requests efficiently

#### Cons:
- ❌ Higher memory usage (each worker loads models)
- ❌ Limited by single instance resources
- ❌ No auto-scaling (Railway replicas are better for this)

#### When to Use:
- Low-medium traffic (< 20 concurrent requests)
- Cost-sensitive deployments
- Predictable traffic patterns

---

### **Solution 3: Warmup Endpoint** (Prevents Cold Starts)

**Best for:** Eliminating cold start latency

We've implemented an automatic warmup system that triggers on page load:

#### Backend: `/api/warmup` Endpoint

**Location:** `src/api/routes/health.py`

```python
@router.get("/warmup")
async def warmup(controller: RetrievalController = Depends(get_retrieval_controller)):
    """
    Warmup endpoint to prevent cold starts.
    Triggers model loading without requiring user data.
    """
    warmup_request = RetrievalRequest(
        query="test",
        context=None,
        user_id=None,  # No user tracking
        session_id=None
    )
    
    await controller.retrieve(warmup_request)
    
    return {
        "status": "warmed_up",
        "models_loaded": True
    }
```

#### Frontend: Automatic Warmup Call

**Location:** `frontend/src/App.jsx`

```javascript
useEffect(() => {
  const warmupServer = async () => {
    try {
      await axios.get('/api/warmup', { timeout: 30000 })
      console.log('Server warmup completed')
    } catch (err) {
      console.warn('Server warmup failed (non-critical):', err.message)
    }
  }

  warmupServer()
}, []) // Run once on page load
```

#### How It Works:

```
User loads page
    ↓
Frontend calls /api/warmup (fire-and-forget)
    ↓
Backend loads all models:
  - sentence-transformers (5-10s)
  - FAISS index (1-2s)
  - TF-IDF vectorizer (<1s)
  - Blocklist/taxonomy (<1s)
    ↓
User's first real query: Fast response! ✅
```

#### Expected Results:

| Scenario | Without Warmup | With Warmup |
|----------|----------------|-------------|
| First request (cold) | 5-15 seconds | ~30ms |
| Subsequent requests | ~30ms | ~30ms |

#### Pros:
- ✅ Eliminates cold start latency
- ✅ Anonymous (no user tracking)
- ✅ Automatic (frontend handles it)
- ✅ Non-blocking (doesn't affect UX)

#### Cons:
- ❌ Doesn't help with concurrent load
- ❌ Only prevents cold starts

---

### **Solution 4: Railway Always-On** (Prevents Container Shutdown)

**Best for:** Production services that need instant availability

Prevent Railway from spinning down your service during idle periods:

#### Steps:
1. Go to Railway Dashboard
2. Select your service
3. Click **Settings** → **Service Settings**
4. Enable **"Always Running"** or set a custom sleep timeout

#### Expected Results:
- First request is never "cold"
- Consistent latency at all times
- No warmup delay

#### Pros:
- ✅ Instant availability
- ✅ Consistent performance

#### Cons:
- ❌ Higher cost (runs 24/7 even when idle)
- ❌ Doesn't help with concurrent load

---

## 📊 Recommended Configuration by Use Case

### **Development/Testing**
```
Configuration: Single instance, 1 worker
Warmup: Enabled
Cost: Minimal
Expected: 30ms sequential, 78ms P95 (< 5 concurrent)
```

### **Low Traffic Production (< 10 concurrent requests)**
```
Configuration: Single instance, 2-4 workers (gunicorn)
Warmup: Enabled
Railway Always-On: Optional
Cost: Low
Expected: 30-60ms P95
```

### **Medium Traffic Production (10-50 concurrent requests)**
```
Configuration: 2-3 Railway replicas
Warmup: Enabled
Railway Always-On: Recommended
Cost: Medium
Expected: 40-70ms P95
```

### **High Traffic Production (50+ concurrent requests)**
```
Configuration: 4+ Railway replicas with auto-scaling
Warmup: Enabled
Railway Always-On: Required
Load Balancer: Railway managed
Cost: High
Expected: 50-90ms P95
```

---

## 🔧 Implementation Checklist

### ✅ Changes Already Made:

- [x] Added `/api/warmup` endpoint in `src/api/routes/health.py`
- [x] Added automatic warmup call in `frontend/src/App.jsx`
- [x] Added gunicorn to `requirements.txt`
- [x] Updated `railway.json` with gunicorn multi-worker command

### 🎯 Next Steps (Choose Based on Your Needs):

#### Option A: Railway Replicas (Recommended for Production)
1. Go to Railway Dashboard
2. Enable 2-3 replicas
3. Deploy and monitor performance
4. Scale up if needed

#### Option B: Gunicorn Multi-Worker (Cost Optimization)
1. Push changes to Railway (already configured in railway.json)
2. Monitor memory usage
3. Adjust worker count based on instance size

#### Option C: Both (Best Performance)
1. Enable Railway replicas (2-3)
2. Use gunicorn multi-worker per replica
3. Maximum concurrent capacity: replicas × workers × 4
   - Example: 3 replicas × 2 workers = handles 24 concurrent requests

---

## 📈 Monitoring & Validation

### Check Current Performance:

```bash
# Test Railway deployment
python scripts/proper_stress_test.py --url https://your-app.railway.app --concurrency 10 --total 100
```

### Monitor Railway Metrics:

1. Go to Railway Dashboard
2. Select your service
3. View **Metrics** tab:
   - CPU usage (should be < 80% avg)
   - Memory usage (should be < 80% of limit)
   - Response time (should be < 100ms P95)
   - Request rate

### Key Metrics to Watch:

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| P95 Latency | < 100ms | Add replicas or workers |
| CPU Usage | < 80% | Add replicas |
| Memory Usage | < 80% | Reduce workers or add replicas |
| Error Rate | < 1% | Investigate logs |

---

## 🐛 Troubleshooting

### Problem: Still seeing 5-15s first request

**Cause:** Cold start, warmup not working

**Solution:**
1. Check browser console for warmup call success
2. Verify `/api/warmup` endpoint is accessible
3. Enable Railway "Always Running"
4. Check Railway logs for model loading errors

### Problem: High latency even with warmup

**Cause:** Concurrent requests hitting GIL

**Solution:**
1. Enable Railway replicas (2-3)
2. Or use gunicorn multi-worker
3. Check if you're sending concurrent requests

### Problem: 502/503 errors during traffic spikes

**Cause:** Instance overloaded

**Solution:**
1. Add more Railway replicas
2. Reduce workers per replica
3. Enable auto-scaling
4. Check memory limits

### Problem: Memory usage keeps growing

**Cause:** Memory leak or too many workers

**Solution:**
1. Reduce number of gunicorn workers
2. Enable Railway auto-restart on memory threshold
3. Check for memory leaks in logs

---

## 📚 Additional Resources

- [Railway Docs: Horizontal Scaling](https://docs.railway.app/reference/scaling)
- [Gunicorn Docs: Worker Configuration](https://docs.gunicorn.org/en/stable/settings.html#workers)
- [FastAPI Deployment Docs](https://fastapi.tiangolo.com/deployment/server-workers/)
- [Performance Testing Guide](../operations/PERFORMANCE.md)

---

## 🎓 Summary

**TL;DR:**

1. **Warmup endpoint** ✅ (Already implemented)
   - Prevents cold starts
   - Automatic on page load
   - No user impact

2. **For Production**: Enable **2-3 Railway replicas**
   - Go to Settings → Replicas
   - Set to 2 or 3
   - Deploy and monitor

3. **For Cost Optimization**: Use **gunicorn multi-worker**
   - Already configured in railway.json
   - Push changes to Railway
   - Monitor memory usage

4. **Monitor Performance**: Use Railway metrics dashboard
   - Watch P95 latency
   - Scale up if > 100ms

**Expected Results:**
- Development: 30ms sequential ✅
- Production (2-3 replicas): 40-70ms P95 ✅
- No more cold starts: Warmup handles it ✅

---

*Last updated: February 24, 2026*

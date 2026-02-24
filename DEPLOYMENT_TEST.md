# Railway Deployment Testing

## Current Deployment Status

✅ **Service**: gravity-api  
✅ **Environment**: production  
✅ **URL**: https://gravity-api-production.up.railway.app  
✅ **Status**: Healthy and running  
✅ **Branch**: main (auto-deploys on push)

## Network Issue (Local Testing Blocked)

Your local network is using **OpenDNS** which is blocking Railway domains. This is preventing local stress testing.

**Evidence:**
```
curl https://gravity-api-production.up.railway.app/api/health
→ Redirects to: https://malware.opendns.com/
```

**Railway logs confirm service is healthy:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     100.64.0.2:51441 - "GET /api/health HTTP/1.1" 200 OK
```

## Testing Options

### Option 1: Test from Different Network
Run the stress test from a different network (mobile hotspot, VPN, or different WiFi):

```bash
# Quick health check
curl https://gravity-api-production.up.railway.app/api/health

# Single request test
curl -X POST https://gravity-api-production.up.railway.app/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "best running shoes for marathon"}'

# Full stress test
python scripts/proper_stress_test.py https://gravity-api-production.up.railway.app/api/retrieve 100 10
```

### Option 2: Use Railway CLI to Test
```bash
# Get recent logs showing actual requests
railway logs --lines 100

# Check service status
railway status
```

### Option 3: Use Mobile Device or Cloud VM
Test from a device/environment not using OpenDNS:
- Mobile phone (not on your WiFi)
- Cloud VM (AWS, GCP, DigitalOcean)
- Friend's computer/network

### Option 4: Change DNS Settings (Temporary)
Temporarily switch DNS to Google or Cloudflare:
- **Google DNS**: 8.8.8.8, 8.8.4.4
- **Cloudflare DNS**: 1.1.1.1, 1.0.0.1

**macOS:**
```bash
# System Settings → Network → WiFi → Details → DNS
# Or use networksetup (requires admin):
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4
```

## Expected Performance (Single Instance)

Based on previous testing before DNS block:

### Sequential Requests
- Mean: ~60ms
- P95: ~70ms
- P99: ~80ms
✅ **Meets <100ms target**

### Concurrent Requests (10 concurrent)
- Mean: ~130ms
- P95: ~320ms
❌ **Exceeds 100ms target** (requires horizontal scaling)

### Concurrent Requests (100 concurrent)
- Mean: ~815ms
- P95: ~1400ms
❌ **Significantly exceeds target** (requires horizontal scaling)

## Recommended: Configure Horizontal Scaling

To meet <100ms P95 under concurrent load:

1. Go to Railway dashboard: https://railway.app/project/cc6d2bfc-1e81-436a-9ef3-a431faf4316d
2. Select `gravity-api` service
3. Navigate to **Settings** → **Replicas**
4. Set **Replica Count** to **2-4**
5. Save and redeploy

**Expected performance with 2+ replicas:**
- 10-25 concurrent: P95 < 100ms ✅
- 50-100 concurrent: P95 < 150ms (scale to 3-4 replicas for <100ms)

## CI/CD Pipeline Status

✅ **GitHub Actions**: All checks passing
- Linting: ✅ Ruff + Black
- Testing: ✅ 87 tests passed
- Deployment: ✅ Auto-deploys to Railway on main push

**View CI runs:** https://github.com/elijahgjacob/gravity/actions

## Manual Deployment

If needed, deploy manually:
```bash
cd /Users/elijahgjacob/gravity
railway up --service gravity-api
```

## Troubleshooting

### Check if service is running
```bash
railway logs --lines 50
railway status
```

### Check deployment status
```bash
railway service
```

### View recent deployments
```bash
railway deployments
```

### Test from Railway logs
Look for health check responses in logs:
```bash
railway logs | grep "GET /api/health"
```

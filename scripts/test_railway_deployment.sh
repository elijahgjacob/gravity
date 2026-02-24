#!/bin/bash

# Test script for Railway deployment
# Run this from a network that doesn't block Railway domains

RAILWAY_URL="https://gravity-api-production.up.railway.app"

echo "================================================================================"
echo "Testing Railway Deployment: $RAILWAY_URL"
echo "================================================================================"
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH=$(curl -s "$RAILWAY_URL/api/health")
if echo "$HEALTH" | jq . > /dev/null 2>&1; then
    echo "✅ Health check passed"
    echo "$HEALTH" | jq .
else
    echo "❌ Health check failed"
    echo "$HEALTH"
    exit 1
fi

echo ""
echo "2. Testing retrieve endpoint (single request)..."
RESPONSE=$(curl -s -X POST "$RAILWAY_URL/api/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"query": "best running shoes for marathon"}')

if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    LATENCY=$(echo "$RESPONSE" | jq -r '.latency_ms')
    CAMPAIGNS=$(echo "$RESPONSE" | jq -r '.campaigns | length')
    echo "✅ Retrieve request successful"
    echo "   Latency: ${LATENCY}ms"
    echo "   Campaigns returned: $CAMPAIGNS"
else
    echo "❌ Retrieve request failed"
    echo "$RESPONSE"
    exit 1
fi

echo ""
echo "3. Running stress test..."
python scripts/proper_stress_test.py "$RAILWAY_URL/api/retrieve" 100 10

echo ""
echo "================================================================================"
echo "Railway deployment test complete!"
echo "================================================================================"

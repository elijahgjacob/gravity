#!/bin/bash
# Monitor Railway deployment and test when ready

URL="https://gravity-api-production.up.railway.app"

echo "Monitoring Railway deployment..."
echo "================================"
echo ""

# Wait for deployment to be ready
attempt=1
max_attempts=60  # 5 minutes (60 × 5 seconds)

while [ $attempt -le $max_attempts ]; do
    echo -n "Attempt $attempt/$max_attempts: "
    
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X GET "$URL/api/health" 2>&1)
    http_code=$(echo "$response" | tail -2 | head -1)
    time_total=$(echo "$response" | tail -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Server is healthy (response time: ${time_total}s)"
        echo ""
        echo "🎉 Deployment is ready! Running quick latency test..."
        echo ""
        
        # Run 10 quick tests
        echo "Sequential Latency Test (10 requests):"
        echo "======================================="
        
        latencies=()
        for i in {1..10}; do
            result=$(curl -s -X POST "$URL/api/retrieve" \
                -H "Content-Type: application/json" \
                -d '{"query": "test"}' 2>&1)
            
            latency=$(echo "$result" | grep -o '"latency_ms":[0-9.]*' | cut -d: -f2)
            
            if [ -n "$latency" ]; then
                echo "  Request $i: ${latency}ms"
                latencies+=($latency)
            else
                echo "  Request $i: ERROR"
            fi
            sleep 0.5
        done
        
        echo ""
        
        # Calculate simple average
        if [ ${#latencies[@]} -gt 0 ]; then
            sum=0
            for lat in "${latencies[@]}"; do
                sum=$(echo "$sum + $lat" | bc)
            done
            avg=$(echo "scale=1; $sum / ${#latencies[@]}" | bc)
            
            echo "Results:"
            echo "  Successful: ${#latencies[@]}/10"
            echo "  Average: ${avg}ms"
            
            if (( $(echo "$avg < 100" | bc -l) )); then
                echo "  ✅ GOOD: Average latency under 100ms"
            else
                echo "  ⚠️  Average latency above 100ms"
            fi
        fi
        
        echo ""
        echo "Run full test with:"
        echo "  python scripts/verify_railway_replicas.py --url $URL --requests 50 --concurrency 10"
        
        exit 0
    else
        echo "⏳ Waiting... (status: $http_code)"
        sleep 5
        ((attempt++))
    fi
done

echo ""
echo "❌ Deployment did not become ready after 5 minutes"
echo "Check Railway dashboard for errors"

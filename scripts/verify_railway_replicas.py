#!/usr/bin/env python3
"""
Verify Railway replicas are working correctly.

This script makes multiple concurrent requests to your Railway deployment
and verifies that they're being distributed across different replicas.

Usage:
    python scripts/verify_railway_replicas.py --url https://your-app.railway.app
    python scripts/verify_railway_replicas.py --url https://your-app.railway.app --requests 50 --concurrency 20
"""

import argparse
import asyncio
import time
from collections import Counter, defaultdict

import httpx


async def make_request(client: httpx.AsyncClient, url: str, request_id: int) -> dict:
    """Make a single request and capture response details."""
    start_time = time.perf_counter()
    
    try:
        response = await client.post(
            f"{url}/api/retrieve",
            json={"query": f"test query {request_id}"},
            timeout=10.0
        )
        
        latency = (time.perf_counter() - start_time) * 1000
        
        return {
            "request_id": request_id,
            "status": response.status_code,
            "latency_ms": latency,
            "server_latency_ms": response.json().get("latency_ms", 0) if response.status_code == 200 else None,
            "headers": dict(response.headers),
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "request_id": request_id,
            "status": 0,
            "latency_ms": (time.perf_counter() - start_time) * 1000,
            "server_latency_ms": None,
            "headers": {},
            "success": False,
            "error": str(e)
        }


async def test_replicas(url: str, total_requests: int = 100, concurrency: int = 10) -> dict:
    """Test Railway replicas with concurrent requests."""
    print(f"\n{'='*60}")
    print(f"  Railway Replica Verification")
    print(f"{'='*60}\n")
    print(f"URL: {url}")
    print(f"Total Requests: {total_requests}")
    print(f"Concurrency: {concurrency}\n")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Make requests in batches based on concurrency
        for batch_start in range(0, total_requests, concurrency):
            batch_end = min(batch_start + concurrency, total_requests)
            batch_size = batch_end - batch_start
            
            print(f"Sending batch {batch_start + 1}-{batch_end}...", end=" ", flush=True)
            
            tasks = [
                make_request(client, url, i)
                for i in range(batch_start, batch_end)
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            success_count = sum(1 for r in batch_results if r["success"])
            print(f"✅ {success_count}/{batch_size} successful")
            
            # Small delay between batches to avoid overwhelming
            if batch_end < total_requests:
                await asyncio.sleep(0.1)
    
    return analyze_results(results)


def analyze_results(results: list[dict]) -> dict:
    """Analyze results to detect replica distribution."""
    print(f"\n{'='*60}")
    print(f"  Results Analysis")
    print(f"{'='*60}\n")
    
    # Basic stats
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print(f"Total Requests:     {total}")
    print(f"Successful:         {successful} ({successful/total*100:.1f}%)")
    print(f"Failed:             {failed} ({failed/total*100:.1f}%)")
    
    # Latency stats (client-side)
    latencies = [r["latency_ms"] for r in results if r["success"]]
    if latencies:
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        
        print(f"\n{'Client-Side Latency (Total Round Trip)':^60}")
        print(f"{'-'*60}")
        print(f"Mean:               {sum(latencies)/len(latencies):.2f}ms")
        print(f"P50:                {p50:.2f}ms")
        print(f"P95:                {p95:.2f}ms {'✅' if p95 < 100 else '❌'} Target: <100ms")
        print(f"P99:                {p99:.2f}ms")
        print(f"Min:                {min(latencies):.2f}ms")
        print(f"Max:                {max(latencies):.2f}ms")
    
    # Server-side latency (from response)
    server_latencies = [r["server_latency_ms"] for r in results if r["server_latency_ms"] is not None]
    if server_latencies:
        server_latencies.sort()
        p50 = server_latencies[int(len(server_latencies) * 0.50)]
        p95 = server_latencies[int(len(server_latencies) * 0.95)]
        
        print(f"\n{'Server-Side Latency (Processing Only)':^60}")
        print(f"{'-'*60}")
        print(f"Mean:               {sum(server_latencies)/len(server_latencies):.2f}ms")
        print(f"P50:                {p50:.2f}ms")
        print(f"P95:                {p95:.2f}ms {'✅' if p95 < 100 else '❌'} Target: <100ms")
    
    # Try to detect replica distribution (Railway adds headers)
    replica_indicators = defaultdict(int)
    
    for result in results:
        if not result["success"]:
            continue
            
        headers = result["headers"]
        
        # Railway may add these headers (check common ones)
        indicators = []
        
        # Check for X-Railway-* headers
        for header, value in headers.items():
            header_lower = header.lower()
            if "railway" in header_lower or "replica" in header_lower or "instance" in header_lower:
                indicators.append(f"{header}: {value}")
        
        # Check for Server/Via headers that might indicate load balancer
        if "server" in headers:
            indicators.append(f"Server: {headers['server']}")
        if "via" in headers:
            indicators.append(f"Via: {headers['via']}")
        
        # If no specific replica identifier, just count by a hash of timing patterns
        # (Different replicas may have slightly different response times)
        if not indicators:
            # Group by approximate server latency (within 5ms buckets)
            if result["server_latency_ms"]:
                bucket = int(result["server_latency_ms"] / 5) * 5
                indicators.append(f"Latency-Bucket-{bucket}ms")
        
        indicator_key = tuple(sorted(indicators)) if indicators else ("unknown",)
        replica_indicators[indicator_key] += 1
    
    # Analyze distribution
    print(f"\n{'Load Distribution Analysis':^60}")
    print(f"{'-'*60}")
    
    if len(replica_indicators) > 1:
        print(f"Detected {len(replica_indicators)} different response patterns")
        print(f"(Likely indicating {len(replica_indicators)} replicas)\n")
        
        for i, (indicator, count) in enumerate(sorted(replica_indicators.items(), key=lambda x: x[1], reverse=True), 1):
            percentage = count / successful * 100
            bar = "█" * int(percentage / 2)
            print(f"Pattern {i}: {count:3d} requests ({percentage:5.1f}%) {bar}")
            if indicator != ("unknown",):
                for ind in indicator:
                    print(f"           {ind}")
        
        # Check if distribution is balanced
        counts = list(replica_indicators.values())
        avg_count = sum(counts) / len(counts)
        max_deviation = max(abs(c - avg_count) for c in counts)
        deviation_pct = (max_deviation / avg_count) * 100
        
        print(f"\n{'Distribution Balance':^60}")
        print(f"{'-'*60}")
        print(f"Average per pattern:  {avg_count:.1f} requests")
        print(f"Max deviation:        {deviation_pct:.1f}%")
        
        if deviation_pct < 20:
            print(f"✅ Well-balanced load distribution")
        elif deviation_pct < 40:
            print(f"⚠️  Moderately balanced (acceptable)")
        else:
            print(f"❌ Unbalanced load distribution")
    else:
        print(f"⚠️  Could not detect multiple replicas")
        print(f"This could mean:")
        print(f"  - Only 1 replica is running")
        print(f"  - Railway load balancer is very sticky")
        print(f"  - Not enough requests to see distribution")
        print(f"\nTip: Try increasing --requests to 100+ and --concurrency to 20+")
    
    # Performance assessment
    print(f"\n{'Performance Assessment':^60}")
    print(f"{'-'*60}")
    
    if successful > 0 and latencies:
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = latencies[int(len(latencies) * 0.95)]
        
        if p95_latency < 100:
            print(f"✅ EXCELLENT: P95 latency under 100ms target")
        elif p95_latency < 150:
            print(f"⚠️  GOOD: P95 latency slightly above target")
        else:
            print(f"❌ NEEDS IMPROVEMENT: P95 latency significantly above target")
        
        # Estimate capacity
        requests_per_sec = successful / (max(latencies) / 1000)
        print(f"\nEstimated Throughput:")
        print(f"  ~{requests_per_sec:.0f} requests/second")
        print(f"  ~{requests_per_sec * 60:.0f} requests/minute")
    
    print(f"\n{'='*60}\n")
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
        "p95_latency": latencies[int(len(latencies) * 0.95)] if latencies else 0,
        "replica_patterns": len(replica_indicators)
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Verify Railway replica distribution")
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Railway deployment URL (e.g., https://your-app.railway.app)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of requests to make (default: 100)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Remove trailing slash from URL
    url = args.url.rstrip("/")
    
    # Check if URL is accessible
    print(f"Checking if {url} is accessible...")
    try:
        import httpx
        response = httpx.get(f"{url}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Server is healthy\n")
        else:
            print(f"⚠️  Server returned status {response.status_code}\n")
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print(f"Make sure the URL is correct and the server is running.\n")
        return
    
    # Run the test
    try:
        asyncio.run(test_replicas(url, args.requests, args.concurrency))
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

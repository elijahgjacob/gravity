#!/usr/bin/env python3
"""
Concurrent stress test for the Ad Retrieval API.

Tests the API under high concurrent load to verify latency remains
under 100ms p95 even with many simultaneous requests.
"""

import asyncio
import json
import statistics
import time

import aiohttp

BASE_URL = "http://localhost:8000"
HEALTH_URL = f"{BASE_URL}/api/health"
RETRIEVE_URL = f"{BASE_URL}/api/retrieve"

# Test queries
TEST_QUERIES = [
    {"query": "best running shoes for marathon"},
    {"query": "laptop for programming"},
    {"query": "wireless headphones"},
    {"query": "yoga mat"},
    {"query": "coffee maker"},
    {"query": "gaming mouse"},
    {"query": "backpack for travel"},
    {"query": "standing desk"},
    {"query": "bluetooth speaker"},
    {"query": "fitness tracker"},
]


async def make_request(session: aiohttp.ClientSession, query: dict) -> dict:
    """Make a single API request and measure latency."""
    start = time.perf_counter()
    try:
        async with session.post(
            RETRIEVE_URL, json=query, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            data = await response.json()
            latency_ms = (time.perf_counter() - start) * 1000
            return {
                "success": response.status == 200,
                "latency_ms": latency_ms,
                "status": response.status,
                "error": None if response.status == 200 else data,
            }
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return {"success": False, "latency_ms": latency_ms, "status": 0, "error": str(e)}


async def run_concurrent_batch(num_concurrent: int, num_requests: int) -> list[dict]:
    """Run a batch of concurrent requests."""
    print(f"\n{'='*80}")
    print(f"Testing with {num_concurrent} concurrent requests ({num_requests} total)")
    print(f"{'='*80}\n")

    results = []

    async with aiohttp.ClientSession() as session:
        # Create batches of concurrent requests
        for batch_num in range(0, num_requests, num_concurrent):
            batch_size = min(num_concurrent, num_requests - batch_num)

            # Create tasks for this batch
            tasks = []
            for i in range(batch_size):
                query = TEST_QUERIES[i % len(TEST_QUERIES)]
                tasks.append(make_request(session, query))

            # Execute batch concurrently
            batch_start = time.perf_counter()
            batch_results = await asyncio.gather(*tasks)
            batch_time = (time.perf_counter() - batch_start) * 1000

            results.extend(batch_results)

            # Progress update
            completed = len(results)
            print(
                f"  Batch {batch_num // num_concurrent + 1}: {batch_size} requests in {batch_time:.2f}ms "
                f"(avg: {batch_time/batch_size:.2f}ms per request) - Total: {completed}/{num_requests}"
            )

    return results


def analyze_results(results: list[dict]) -> dict:
    """Analyze and print results."""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    latencies = [r["latency_ms"] for r in successful]

    if not latencies:
        print("\n❌ No successful requests!")
        return {}

    stats = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "p90": (
            statistics.quantiles(latencies, n=100)[89] if len(latencies) >= 10 else max(latencies)
        ),
        "p95": (
            statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 20 else max(latencies)
        ),
        "p99": (
            statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        ),
        "min": min(latencies),
        "max": max(latencies),
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
    }

    print(f"\n{'='*80}")
    print("  Results Summary")
    print(f"{'='*80}\n")

    print(f"Total Requests:     {stats['total']:>6}")
    print(f"Successful:         {stats['successful']:>6}")
    print(f"Failed:             {stats['failed']:>6}")
    print(f"Success Rate:       {stats['successful']/stats['total']*100:>5.1f}%")

    print(f"\n{'Latency Statistics':^80}")
    print(f"{'-'*80}")
    print(f"Mean:               {stats['mean']:>6.2f}ms")
    print(f"Median (P50):       {stats['median']:>6.2f}ms")
    print(f"P90:                {stats['p90']:>6.2f}ms")
    print(
        f"P95:                {stats['p95']:>6.2f}ms  {'✅' if stats['p95'] < 100 else '❌'} Target: <100ms"
    )
    print(f"P99:                {stats['p99']:>6.2f}ms")
    print(f"Min:                {stats['min']:>6.2f}ms")
    print(f"Max:                {stats['max']:>6.2f}ms")
    print(f"Std Dev:            {stats['stdev']:>6.2f}ms")

    if failed:
        print(f"\n{'Failed Requests':^80}")
        print(f"{'-'*80}")
        for i, fail in enumerate(failed[:5], 1):
            print(f"{i}. Status: {fail['status']}, Error: {fail['error']}")
        if len(failed) > 5:
            print(f"... and {len(failed) - 5} more failures")

    print(f"\n{'='*80}\n")

    return stats


async def main():
    """Run stress tests with increasing concurrency."""
    print("\n" + "=" * 80)
    print("  CONCURRENT STRESS TEST - Ad Retrieval API")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Queries: {len(TEST_QUERIES)}")

    # Check health first
    print("\nChecking API health...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(HEALTH_URL) as response:
                health = await response.json()
                print(f"✓ API is healthy: {health}")
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return

    # Test scenarios with increasing concurrency
    test_scenarios = [
        (10, 100),  # 10 concurrent, 100 total
        (25, 250),  # 25 concurrent, 250 total
        (50, 500),  # 50 concurrent, 500 total
        (100, 1000),  # 100 concurrent, 1000 total
    ]

    all_results = {}

    for concurrent, total in test_scenarios:
        results = await run_concurrent_batch(concurrent, total)
        stats = analyze_results(results)
        all_results[f"{concurrent}_concurrent"] = stats

        # Brief pause between scenarios
        await asyncio.sleep(2)

    # Final summary
    print(f"\n{'='*80}")
    print("  FINAL SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Concurrency':<15} {'Total':<10} {'P50':<12} {'P95':<12} {'P99':<12} {'Status':<10}")
    print(f"{'-'*80}")

    for (concurrent, total), (key, stats) in zip(test_scenarios, all_results.items()):
        if stats:
            status = "✅ PASS" if stats["p95"] < 100 else "❌ FAIL"
            print(
                f"{concurrent:<15} {total:<10} {stats['median']:>6.2f}ms    {stats['p95']:>6.2f}ms    {stats['p99']:>6.2f}ms    {status}"
            )

    print(f"\n{'='*80}\n")

    # Save results
    with open("concurrent_stress_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Results saved to concurrent_stress_results.json")


if __name__ == "__main__":
    asyncio.run(main())

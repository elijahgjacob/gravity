#!/usr/bin/env python3
"""
Proper concurrent stress test that measures individual request latencies.
"""

import asyncio
import json
import statistics
import time

import aiohttp

BASE_URL = "http://localhost:8000"
RETRIEVE_URL = f"{BASE_URL}/api/retrieve"

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


async def make_request(session: aiohttp.ClientSession, query: dict, request_id: int) -> dict:
    """Make a single API request and extract server-side latency."""
    client_start = time.perf_counter()
    try:
        async with session.post(
            RETRIEVE_URL, json=query, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            data = await response.json()
            client_latency = (time.perf_counter() - client_start) * 1000

            # Use server-reported latency (more accurate)
            server_latency = data.get("latency_ms", client_latency)

            return {
                "success": response.status == 200,
                "server_latency_ms": server_latency,
                "client_latency_ms": client_latency,
                "status": response.status,
                "request_id": request_id,
                "error": None,
            }
    except Exception as e:
        client_latency = (time.perf_counter() - client_start) * 1000
        return {
            "success": False,
            "server_latency_ms": client_latency,
            "client_latency_ms": client_latency,
            "status": 0,
            "request_id": request_id,
            "error": str(e),
        }


async def run_concurrent_test(num_concurrent: int, num_total: int) -> list[dict]:
    """Run concurrent requests and measure latencies."""
    print(f"\n{'='*80}")
    print(f"Testing: {num_concurrent} concurrent requests, {num_total} total")
    print(f"{'='*80}\n")

    results = []

    async with aiohttp.ClientSession() as session:
        # Create all tasks upfront
        tasks = []
        for i in range(num_total):
            query = TEST_QUERIES[i % len(TEST_QUERIES)]
            tasks.append(make_request(session, query, i))

        # Execute in batches
        batch_size = num_concurrent
        for batch_start in range(0, num_total, batch_size):
            batch_end = min(batch_start + batch_size, num_total)
            batch_tasks = tasks[batch_start:batch_end]

            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

            print(f"  Completed {len(results)}/{num_total} requests...")

    return results


def analyze_results(results: list[dict], label: str):
    """Analyze and print results."""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if not successful:
        print(f"\n❌ No successful requests for {label}!")
        return None

    server_latencies = [r["server_latency_ms"] for r in successful]

    stats = {
        "label": label,
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "mean": statistics.mean(server_latencies),
        "median": statistics.median(server_latencies),
        "p90": (
            statistics.quantiles(server_latencies, n=100)[89]
            if len(server_latencies) >= 10
            else max(server_latencies)
        ),
        "p95": (
            statistics.quantiles(server_latencies, n=100)[94]
            if len(server_latencies) >= 20
            else max(server_latencies)
        ),
        "p99": (
            statistics.quantiles(server_latencies, n=100)[98]
            if len(server_latencies) >= 100
            else max(server_latencies)
        ),
        "min": min(server_latencies),
        "max": max(server_latencies),
        "stdev": statistics.stdev(server_latencies) if len(server_latencies) > 1 else 0,
    }

    print(f"\n{label}")
    print(f"{'-'*80}")
    print(
        f"Success Rate: {stats['successful']}/{stats['total']} ({stats['successful']/stats['total']*100:.1f}%)"
    )
    print(f"Mean:         {stats['mean']:>6.2f}ms")
    print(f"Median (P50): {stats['median']:>6.2f}ms")
    print(f"P90:          {stats['p90']:>6.2f}ms")
    print(
        f"P95:          {stats['p95']:>6.2f}ms  {'✅' if stats['p95'] < 100 else '❌'} Target: <100ms"
    )
    print(f"P99:          {stats['p99']:>6.2f}ms")
    print(f"Min:          {stats['min']:>6.2f}ms")
    print(f"Max:          {stats['max']:>6.2f}ms")

    return stats


async def main():
    """Run stress tests."""
    print("\n" + "=" * 80)
    print("  CONCURRENT STRESS TEST - Individual Request Latencies")
    print("=" * 80)

    test_scenarios = [
        (10, 100),
        (25, 250),
        (50, 500),
        (100, 1000),
    ]

    all_stats = []

    for concurrent, total in test_scenarios:
        results = await run_concurrent_test(concurrent, total)
        stats = analyze_results(results, f"{concurrent} concurrent ({total} total)")
        if stats:
            all_stats.append(stats)
        await asyncio.sleep(2)

    # Final summary
    print(f"\n{'='*80}")
    print("  FINAL SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Concurrency':<15} {'Total':<10} {'Mean':<12} {'P50':<12} {'P95':<12} {'Status':<10}")
    print(f"{'-'*80}")

    for stats in all_stats:
        status = "✅ PASS" if stats["p95"] < 100 else "❌ FAIL"
        label = stats["label"].split("(")[0].strip()
        print(
            f"{label:<15} {stats['total']:<10} {stats['mean']:>6.2f}ms    {stats['median']:>6.2f}ms    {stats['p95']:>6.2f}ms    {status}"
        )

    print(f"\n{'='*80}\n")

    # Save results
    with open("proper_stress_results.json", "w") as f:
        json.dump(all_stats, f, indent=2)
    print("Results saved to proper_stress_results.json")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Benchmark script for Ad Retrieval API.

Measures latency statistics (mean, median, P95, P99) across test queries.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --runs 100
    python scripts/benchmark.py --queries tests/test_queries.json
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import requests

# Add project root to path if running from scripts directory
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def load_test_queries(filepath: str = "tests/test_queries.json") -> list[dict]:
    """Load test queries from JSON file."""
    # Try relative to current directory first
    path = Path(filepath)
    if not path.exists():
        # Try relative to project root
        path = project_root / filepath

    with open(path) as f:
        return json.load(f)


def benchmark_latency(
    test_queries: list[dict], n_runs: int = 100, base_url: str = "http://localhost:8000"
) -> dict:
    """
    Benchmark API latency across multiple runs.

    Args:
        test_queries: List of test query dictionaries
        n_runs: Number of times to run each query
        base_url: Base URL of the API

    Returns:
        Dictionary with latency statistics
    """
    print(f"\n{'='*60}")
    print("  Ad Retrieval API Benchmark")
    print(f"{'='*60}\n")
    print(f"Test Queries: {len(test_queries)}")
    print(f"Runs per Query: {n_runs}")
    print(f"Total Requests: {len(test_queries) * n_runs}")
    print(f"Base URL: {base_url}\n")

    latencies = []
    short_circuit_latencies = []
    full_pipeline_latencies = []
    errors = 0

    print("Running benchmark...")
    start_time = time.perf_counter()

    for i, test in enumerate(test_queries, 1):
        query_latencies = []

        for run in range(n_runs):
            try:
                payload = {"query": test["query"]}
                if test.get("context"):
                    payload["context"] = test["context"]

                response = requests.post(f"{base_url}/api/retrieve", json=payload, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    latency = data["latency_ms"]
                    latencies.append(latency)
                    query_latencies.append(latency)

                    # Track short-circuit vs full pipeline
                    if data.get("metadata", {}).get("short_circuited"):
                        short_circuit_latencies.append(latency)
                    else:
                        full_pipeline_latencies.append(latency)
                else:
                    errors += 1

            except Exception as e:
                errors += 1
                print(f"  Error on query {i}, run {run+1}: {e}")

        # Print progress
        if query_latencies:
            avg = statistics.mean(query_latencies)
            print(f"  Query {i}/{len(test_queries)}: {test['name'][:40]:<40} Avg: {avg:6.2f}ms")

    elapsed = time.perf_counter() - start_time

    # Calculate statistics
    if not latencies:
        print("\n❌ No successful requests!")
        return {}

    stats = {
        "total_requests": len(test_queries) * n_runs,
        "successful_requests": len(latencies),
        "failed_requests": errors,
        "total_time_seconds": elapsed,
        "requests_per_second": len(latencies) / elapsed,
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "stddev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
    }

    # Calculate percentiles
    sorted_latencies = sorted(latencies)
    stats["p50_ms"] = sorted_latencies[int(len(sorted_latencies) * 0.50)]
    stats["p90_ms"] = sorted_latencies[int(len(sorted_latencies) * 0.90)]
    stats["p95_ms"] = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    stats["p99_ms"] = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    # Short-circuit vs full pipeline stats
    if short_circuit_latencies:
        stats["short_circuit_mean_ms"] = statistics.mean(short_circuit_latencies)
        stats["short_circuit_count"] = len(short_circuit_latencies)

    if full_pipeline_latencies:
        stats["full_pipeline_mean_ms"] = statistics.mean(full_pipeline_latencies)
        stats["full_pipeline_count"] = len(full_pipeline_latencies)

    return stats


def print_results(stats: dict):
    """Print benchmark results in a formatted table."""
    print(f"\n{'='*60}")
    print("  Benchmark Results")
    print(f"{'='*60}\n")

    print(f"Total Requests:      {stats['total_requests']:>10,}")
    print(f"Successful:          {stats['successful_requests']:>10,}")
    print(f"Failed:              {stats['failed_requests']:>10,}")
    print(f"Total Time:          {stats['total_time_seconds']:>10.2f}s")
    print(f"Requests/Second:     {stats['requests_per_second']:>10.2f}")

    print(f"\n{'Latency Statistics':^60}")
    print(f"{'-'*60}")
    print(f"Mean:                {stats['mean_ms']:>10.2f}ms")
    print(f"Median (P50):        {stats['p50_ms']:>10.2f}ms")
    print(f"P90:                 {stats['p90_ms']:>10.2f}ms")
    print(
        f"P95:                 {stats['p95_ms']:>10.2f}ms  {'✅ Target: <100ms' if stats['p95_ms'] < 100 else '❌ Target: <100ms'}"
    )
    print(f"P99:                 {stats['p99_ms']:>10.2f}ms")
    print(f"Min:                 {stats['min_ms']:>10.2f}ms")
    print(f"Max:                 {stats['max_ms']:>10.2f}ms")
    print(f"Std Dev:             {stats['stddev_ms']:>10.2f}ms")

    if "short_circuit_mean_ms" in stats:
        print(f"\n{'Pipeline Breakdown':^60}")
        print(f"{'-'*60}")
        print(
            f"Short-Circuit Avg:   {stats['short_circuit_mean_ms']:>10.2f}ms  ({stats['short_circuit_count']} requests)"
        )
        print(
            f"Full Pipeline Avg:   {stats['full_pipeline_mean_ms']:>10.2f}ms  ({stats['full_pipeline_count']} requests)"
        )

    # Performance assessment
    print(f"\n{'Performance Assessment':^60}")
    print(f"{'-'*60}")

    if stats["p95_ms"] < 100:
        print("✅ EXCELLENT: P95 latency under 100ms target")
    elif stats["p95_ms"] < 150:
        print("⚠️  GOOD: P95 latency slightly above target")
    else:
        print("❌ NEEDS IMPROVEMENT: P95 latency significantly above target")

    if stats["mean_ms"] < 50:
        print("✅ EXCELLENT: Mean latency under 50ms")
    elif stats["mean_ms"] < 100:
        print("✅ GOOD: Mean latency under 100ms")

    print(f"\n{'='*60}\n")


def save_results(stats: dict, output_file: str = "benchmark_results.json"):
    """Save benchmark results to JSON file."""
    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Results saved to {output_file}")


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description="Benchmark Ad Retrieval API")
    parser.add_argument(
        "--runs", type=int, default=100, help="Number of runs per query (default: 100)"
    )
    parser.add_argument(
        "--queries",
        type=str,
        default="tests/test_queries.json",
        help="Path to test queries JSON file",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file for results (default: benchmark_results.json)",
    )

    args = parser.parse_args()

    # Check if API is accessible
    try:
        response = requests.get(f"{args.url}/api/health", timeout=5)
        if response.status_code not in [200, 500]:  # 500 is ok for now
            print(f"⚠️  Warning: API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to API at {args.url}")
        print("   Make sure the server is running:")
        print("   python -m uvicorn src.api.main:app --reload\n")
        return
    except Exception as e:
        print(f"\n❌ Error checking API: {e}\n")
        return

    # Load test queries
    try:
        test_queries = load_test_queries(args.queries)
    except FileNotFoundError:
        print(f"\n❌ Error: Test queries file not found: {args.queries}\n")
        return
    except Exception as e:
        print(f"\n❌ Error loading test queries: {e}\n")
        return

    # Run benchmark
    stats = benchmark_latency(test_queries, args.runs, args.url)

    if stats:
        print_results(stats)
        save_results(stats, args.output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick test script for the Ad Retrieval API.

Usage:
    python test_api.py
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint."""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_readiness():
    """Test readiness endpoint."""
    print_section("2. Readiness Check")
    response = requests.get(f"{BASE_URL}/api/ready")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_retrieve(query: str, context: Optional[dict] = None, description: str = ""):
    """Test retrieval endpoint."""
    print_section(f"3. Retrieval Test: {description}")
    
    payload = {"query": query}
    if context:
        payload["context"] = context
    
    print(f"Query: '{query}'")
    if context:
        print(f"Context: {json.dumps(context, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/retrieve",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Results:")
        print(f"   Ad Eligibility: {data['ad_eligibility']:.2f}")
        print(f"   Categories: {data['extracted_categories'][:5]}")
        print(f"   Campaigns Returned: {len(data['campaigns'])}")
        print(f"   Latency: {data['latency_ms']:.2f}ms")
        
        if data['campaigns']:
            print(f"\n   Top 3 Campaigns:")
            for i, campaign in enumerate(data['campaigns'][:3], 1):
                print(f"   {i}. {campaign['title']}")
                print(f"      Category: {campaign['category']}")
                print(f"      Relevance: {campaign['relevance_score']:.3f}")
        
        print(f"\n   Metadata: {json.dumps(data['metadata'], indent=6)}")
    else:
        print(f"❌ Error: {response.text}")


def main():
    """Run all tests."""
    print("\n" + "🚀 Ad Retrieval API Test Suite ".center(60, "="))
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Readiness check
        test_readiness()
        
        # Test 3: Commercial query
        test_retrieve(
            query="Best running shoes for marathon training",
            context={
                "age": 30,
                "gender": "male",
                "location": "San Francisco, CA",
                "interests": ["fitness", "running", "health"]
            },
            description="Commercial Query with Context"
        )
        
        # Test 4: Blocked query (should short-circuit)
        print_section("4. Blocked Query Test")
        test_retrieve(
            query="I want to commit suicide",
            description="Blocked Query (Short-Circuit)"
        )
        
        # Test 5: Informational query
        print_section("5. Informational Query Test")
        test_retrieve(
            query="What is the history of marathon running?",
            description="Informational Query"
        )
        
        # Test 6: Product query without context
        print_section("6. Product Query (No Context)")
        test_retrieve(
            query="laptop for programming",
            description="Product Query"
        )
        
        # Test 7: Fitness query
        print_section("7. Fitness Query")
        test_retrieve(
            query="yoga mat and fitness tracker",
            context={
                "age": 35,
                "gender": "female",
                "interests": ["yoga", "wellness", "fitness"]
            },
            description="Multi-Product Fitness Query"
        )
        
        print("\n" + "✅ All Tests Complete! ".center(60, "=") + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server.")
        print("   Make sure the server is running: uvicorn src.api.main:app --reload\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()

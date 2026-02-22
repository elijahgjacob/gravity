"""Quick test script to verify API server is working.

IMPORTANT: Start the server first in a separate terminal:
    uvicorn src.api.main:app --reload

Then run this script:
    python scripts/test_api_server.py
"""

import sys
import requests
import json


def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("API SERVER TEST")
    print("=" * 60)
    print("\nℹ️  Make sure the server is running in another terminal:")
    print("   uvicorn src.api.main:app --reload")
    print()
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection refused - Server is not running!")
        print()
        print("   Start the server first:")
        print("   1. Open a new terminal")
        print("   2. cd /Users/elijahgjacob/gravity")
        print("   3. source venv/bin/activate")
        print("   4. uvicorn src.api.main:app --reload")
        print()
        print("   Then run this script again.")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    
    # Test 2: Health check
    print("\n2. Testing health endpoint...")
    response = requests.get(f"{base_url}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    print(f"   Latency: {response.headers.get('X-Latency-Ms')}ms")
    
    # Test 3: Readiness check
    print("\n3. Testing readiness endpoint...")
    response = requests.get(f"{base_url}/api/ready")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 4: Retrieve endpoint
    print("\n4. Testing retrieve endpoint...")
    request_data = {
        "query": "I'm running a marathon next month and need new shoes",
        "context": {
            "gender": "male",
            "age": 24,
            "location": "San Francisco, CA",
            "interests": ["fitness", "outdoor activities"]
        }
    }
    
    response = requests.post(f"{base_url}/api/retrieve", json=request_data)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Ad Eligibility: {data['ad_eligibility']}")
    print(f"   Categories: {data['extracted_categories']}")
    print(f"   Campaigns: {len(data['campaigns'])}")
    print(f"   Latency: {data['latency_ms']}ms")
    print(f"   Metadata: {json.dumps(data['metadata'], indent=2)}")
    
    # Test 5: OpenAPI docs
    print("\n5. Testing OpenAPI documentation...")
    response = requests.get(f"{base_url}/openapi.json")
    print(f"   Status: {response.status_code}")
    schema = response.json()
    print(f"   API Title: {schema['info']['title']}")
    print(f"   API Version: {schema['info']['version']}")
    print(f"   Endpoints: {len(schema['paths'])} paths")
    
    print("\n" + "=" * 60)
    print("✅ ALL API TESTS PASSED")
    print("=" * 60)
    print(f"\nAPI Documentation: {base_url}/docs")
    print(f"ReDoc: {base_url}/redoc")


if __name__ == "__main__":
    test_api()

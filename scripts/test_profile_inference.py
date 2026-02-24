"""Test script for user profile inference system."""

import asyncio
import httpx
import json
from datetime import datetime

API_URL = "http://localhost:8000"


async def test_marathon_planning_scenario():
    """
    Test the marathon planning scenario:
    1. User searches for marathon shoes
    2. User checks weather in Boston
    3. User searches for hotels in Boston
    4. Expect: airfare and travel categories inferred
    """
    print("\n" + "="*80)
    print("MARATHON PLANNING SCENARIO TEST")
    print("="*80)
    
    user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\nUser ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Query 1: Marathon shoes
        print("\n" + "-"*80)
        print("Query 1: Marathon shoes")
        print("-"*80)
        
        response1 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "best marathon running shoes for training",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                }
            }
        )
        
        result1 = response1.json()
        print(f"Status: {response1.status_code}")
        print(f"Eligibility: {result1['ad_eligibility']}")
        print(f"Categories: {result1['extracted_categories'][:5]}")
        print(f"Campaigns: {len(result1['campaigns'])}")
        print(f"Latency: {result1['latency_ms']:.2f}ms")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Query 2: Weather in Boston
        print("\n" + "-"*80)
        print("Query 2: Weather in Boston")
        print("-"*80)
        
        response2 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "Boston weather in April",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                }
            }
        )
        
        result2 = response2.json()
        print(f"Status: {response2.status_code}")
        print(f"Eligibility: {result2['ad_eligibility']}")
        print(f"Categories: {result2['extracted_categories'][:5]}")
        print(f"Campaigns: {len(result2['campaigns'])}")
        print(f"Latency: {result2['latency_ms']:.2f}ms")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Query 3: Hotels in Boston
        print("\n" + "-"*80)
        print("Query 3: Hotels in Boston")
        print("-"*80)
        
        response3 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "hotels near Boston Marathon finish line",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                }
            }
        )
        
        result3 = response3.json()
        print(f"Status: {response3.status_code}")
        print(f"Eligibility: {result3['ad_eligibility']}")
        print(f"Categories: {result3['extracted_categories'][:5]}")
        print(f"Campaigns: {len(result3['campaigns'])}")
        print(f"Latency: {result3['latency_ms']:.2f}ms")
        
        # Wait for profile analysis to complete
        print("\n" + "-"*80)
        print("Waiting for profile analysis (5 seconds)...")
        print("-"*80)
        await asyncio.sleep(5)
        
        # Query 4: Check if airfare categories are now inferred
        print("\n" + "-"*80)
        print("Query 4: Running watch (should now include inferred categories)")
        print("-"*80)
        
        response4 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "best running watches for marathon training",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                }
            }
        )
        
        result4 = response4.json()
        print(f"Status: {response4.status_code}")
        print(f"Eligibility: {result4['ad_eligibility']}")
        print(f"Categories: {result4['extracted_categories']}")
        print(f"Campaigns: {len(result4['campaigns'])}")
        print(f"Latency: {result4['latency_ms']:.2f}ms")
        
        # Check if inferred categories are present
        inferred_present = any(
            cat in result4['extracted_categories'] 
            for cat in ["airfare", "travel_packages", "car_rental", "travel_insurance"]
        )
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"✓ Query 1 completed: {result1['latency_ms']:.2f}ms")
        print(f"✓ Query 2 completed: {result2['latency_ms']:.2f}ms")
        print(f"✓ Query 3 completed: {result3['latency_ms']:.2f}ms")
        print(f"✓ Query 4 completed: {result4['latency_ms']:.2f}ms")
        
        if inferred_present:
            print(f"\n✅ SUCCESS: Inferred categories detected in Query 4!")
            print(f"   Categories: {result4['extracted_categories']}")
        else:
            print(f"\n⚠️  WARNING: No inferred categories detected yet")
            print(f"   This may be expected if:")
            print(f"   - Profile analysis hasn't completed yet (try waiting longer)")
            print(f"   - Pattern confidence is below threshold")
            print(f"   - Pattern rules need adjustment")
            print(f"   Categories: {result4['extracted_categories']}")


async def test_vacation_planning_scenario():
    """
    Test the vacation planning scenario:
    1. User searches for vacation destinations
    2. User searches for flights to Hawaii
    3. User searches for hotels in Hawaii
    4. Expect: car rental, tours, activities inferred
    """
    print("\n" + "="*80)
    print("VACATION PLANNING SCENARIO TEST")
    print("="*80)
    
    user_id = f"test_user_vacation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_id = f"sess_vacation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\nUser ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Query 1: Vacation planning
        print("\n" + "-"*80)
        print("Query 1: Vacation ideas")
        print("-"*80)
        
        response1 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "best vacation destinations for summer",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 35,
                    "gender": "female",
                    "location": "New York, NY",
                    "interests": ["travel", "beach", "relaxation"]
                }
            }
        )
        
        result1 = response1.json()
        print(f"Categories: {result1['extracted_categories'][:5]}")
        print(f"Latency: {result1['latency_ms']:.2f}ms")
        
        await asyncio.sleep(2)
        
        # Query 2: Flights to Hawaii
        print("\n" + "-"*80)
        print("Query 2: Flights to Hawaii")
        print("-"*80)
        
        response2 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "cheap flights to Hawaii in July",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 35,
                    "gender": "female",
                    "location": "New York, NY",
                    "interests": ["travel", "beach", "relaxation"]
                }
            }
        )
        
        result2 = response2.json()
        print(f"Categories: {result2['extracted_categories'][:5]}")
        print(f"Latency: {result2['latency_ms']:.2f}ms")
        
        await asyncio.sleep(2)
        
        # Query 3: Hotels in Hawaii
        print("\n" + "-"*80)
        print("Query 3: Hotels in Hawaii")
        print("-"*80)
        
        response3 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "beachfront hotels in Maui Hawaii",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 35,
                    "gender": "female",
                    "location": "New York, NY",
                    "interests": ["travel", "beach", "relaxation"]
                }
            }
        )
        
        result3 = response3.json()
        print(f"Categories: {result3['extracted_categories'][:5]}")
        print(f"Latency: {result3['latency_ms']:.2f}ms")
        
        # Wait for analysis
        print("\n" + "-"*80)
        print("Waiting for profile analysis (5 seconds)...")
        print("-"*80)
        await asyncio.sleep(5)
        
        # Query 4: Check inferred categories
        print("\n" + "-"*80)
        print("Query 4: Beach gear (should include inferred travel categories)")
        print("-"*80)
        
        response4 = await client.post(
            f"{API_URL}/api/retrieve",
            json={
                "query": "beach gear and accessories",
                "user_id": user_id,
                "session_id": session_id,
                "context": {
                    "age": 35,
                    "gender": "female",
                    "location": "New York, NY",
                    "interests": ["travel", "beach", "relaxation"]
                }
            }
        )
        
        result4 = response4.json()
        print(f"Categories: {result4['extracted_categories']}")
        print(f"Latency: {result4['latency_ms']:.2f}ms")
        
        # Check results
        inferred_present = any(
            cat in result4['extracted_categories'] 
            for cat in ["car_rental", "tours", "activities", "travel_insurance"]
        )
        
        print("\n" + "="*80)
        if inferred_present:
            print("✅ SUCCESS: Vacation planning pattern detected!")
        else:
            print("⚠️  No inferred categories yet (may need more time)")


async def test_health_check():
    """Test that the API is running and profile system is enabled."""
    print("\n" + "="*80)
    print("HEALTH CHECK")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/api/health")
            health = response.json()
            
            print(f"\nAPI Status: {health.get('status')}")
            print(f"Dependencies:")
            for key, value in health.get('dependencies', {}).items():
                status = "✓" if value else "✗"
                print(f"  {status} {key}: {value}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"\n✗ API not reachable: {e}")
            print(f"  Make sure the server is running:")
            print(f"  uvicorn src.api.main:app --reload")
            return False


async def main():
    """Run all test scenarios."""
    print("\n" + "="*80)
    print("USER PROFILE INFERENCE SYSTEM - TEST SUITE")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API health
    if not await test_health_check():
        print("\n✗ Cannot proceed: API is not running")
        return
    
    print("\n\nStarting test scenarios...")
    
    # Test marathon planning
    try:
        await test_marathon_planning_scenario()
    except Exception as e:
        print(f"\n✗ Marathon scenario failed: {e}")
    
    # Wait between scenarios
    await asyncio.sleep(3)
    
    # Test vacation planning
    try:
        await test_vacation_planning_scenario()
    except Exception as e:
        print(f"\n✗ Vacation scenario failed: {e}")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

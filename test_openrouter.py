#!/usr/bin/env python3
"""Test script to verify OpenRouter API connectivity."""

import os
import requests
import urllib3
from dotenv import load_dotenv

# Disable SSL warnings for testing (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

def test_openrouter_connection():
    """Test basic connectivity to OpenRouter API."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in environment")
        return False
    
    print(f"✓ API key loaded (ends with: ...{api_key[-8:]})")
    
    # Test endpoint - simple completion request
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Say 'Hello, OpenRouter is working!' if you can read this."}
        ],
        "max_tokens": 50
    }
    
    print("\n🔄 Testing OpenRouter API connection...")
    print(f"Endpoint: {url}")
    
    try:
        # Note: verify=False is used due to SSL cert issues on macOS
        # For production, fix SSL certificates properly
        response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"\n✅ Success! API Response:\n{message}\n")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}\n")
        return False

if __name__ == "__main__":
    success = test_openrouter_connection()
    exit(0 if success else 1)

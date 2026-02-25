#!/usr/bin/env python3
"""
Verification script for Graphiti initialization fix.

This script demonstrates the correct way to initialize OpenAIClient
in graphiti-core 0.28.1.

The issue: OpenAIClient no longer accepts direct keyword arguments for
api_key, base_url, and model. Instead, these must be wrapped in a LLMConfig object.

Fix: Create LLMConfig with the configuration, then pass it to OpenAIClient.
"""

def test_graphiti_initialization():
    """Test that Graphiti can be initialized with OpenRouter."""
    try:
        from graphiti_core import Graphiti
        from graphiti_core.llm_client import OpenAIClient
        from graphiti_core.llm_client.config import LLMConfig
        
        print("✓ Graphiti imports successful")
        
        # Correct way to initialize (post-fix)
        llm_config = LLMConfig(
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3.5-sonnet"
        )
        llm_client = OpenAIClient(config=llm_config)
        
        print("✓ OpenAIClient initialized successfully with LLMConfig")
        print("\nFix verified: LLMConfig approach works correctly")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Note: graphiti-core requires Python 3.10+")
        return False
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return False


if __name__ == "__main__":
    print("Verifying Graphiti initialization fix...")
    print("=" * 60)
    test_graphiti_initialization()

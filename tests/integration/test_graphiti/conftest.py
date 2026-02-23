"""Pytest fixtures for Graphiti integration tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def mock_graphiti_client():
    """Mock Graphiti client for testing."""
    mock_client = MagicMock()
    mock_client.add_episode = AsyncMock()
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    return MagicMock()


@pytest.fixture
def graphiti_test_config():
    """Test configuration for Graphiti."""
    return {
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "test_password",
        "openrouter_api_key": "sk-test-key",
        "llm_model": "anthropic/claude-3.5-sonnet",
        "namespace": "test_ad_retrieval"
    }


@pytest.fixture
def sample_query_event():
    """Sample query event for testing."""
    return {
        "query": "running shoes for marathon",
        "context": {
            "age": 30,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness", "running"]
        },
        "eligibility": 0.95,
        "categories": ["running_shoes", "marathon_gear"],
        "campaigns": [
            {
                "campaign_id": "camp_123",
                "position": 0,
                "relevance_score": 0.94,
                "category": "running_shoes"
            }
        ]
    }

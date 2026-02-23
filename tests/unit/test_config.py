"""Unit tests for configuration settings."""

import os
import pytest
from pydantic import ValidationError
from src.core.config import Settings


class TestGraphitiConfiguration:
    """Test Graphiti-related configuration settings."""
    
    def test_default_graphiti_settings(self):
        """Test that Graphiti settings have correct defaults."""
        settings = Settings()
        
        assert settings.GRAPHITI_ENABLED is False
        assert settings.GRAPHITI_NEO4J_URI == "bolt://localhost:7687"
        assert settings.GRAPHITI_NEO4J_USER == "neo4j"
        assert settings.GRAPHITI_NEO4J_PASSWORD == "password"
        assert settings.OPENROUTER_API_KEY == ""
        assert settings.GRAPHITI_LLM_MODEL == "anthropic/claude-3.5-sonnet"
        assert settings.GRAPHITI_NAMESPACE == "ad_retrieval"
    
    def test_graphiti_enabled_from_env(self, monkeypatch):
        """Test that GRAPHITI_ENABLED can be set via environment variable."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "true")
        settings = Settings()
        
        assert settings.GRAPHITI_ENABLED is True
    
    def test_graphiti_disabled_from_env(self, monkeypatch):
        """Test that GRAPHITI_ENABLED can be disabled via environment variable."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "false")
        settings = Settings()
        
        assert settings.GRAPHITI_ENABLED is False
    
    def test_neo4j_uri_from_env(self, monkeypatch):
        """Test that Neo4j URI can be set via environment variable."""
        test_uri = "bolt://production-neo4j:7687"
        monkeypatch.setenv("GRAPHITI_NEO4J_URI", test_uri)
        settings = Settings()
        
        assert settings.GRAPHITI_NEO4J_URI == test_uri
    
    def test_neo4j_credentials_from_env(self, monkeypatch):
        """Test that Neo4j credentials can be set via environment variables."""
        test_user = "admin"
        test_password = "secure_password_123"
        
        monkeypatch.setenv("GRAPHITI_NEO4J_USER", test_user)
        monkeypatch.setenv("GRAPHITI_NEO4J_PASSWORD", test_password)
        settings = Settings()
        
        assert settings.GRAPHITI_NEO4J_USER == test_user
        assert settings.GRAPHITI_NEO4J_PASSWORD == test_password
    
    def test_openrouter_api_key_from_env(self, monkeypatch):
        """Test that OpenRouter API key can be set via environment variable."""
        test_key = "sk-or-v1-test-key-12345"
        monkeypatch.setenv("OPENROUTER_API_KEY", test_key)
        settings = Settings()
        
        assert settings.OPENROUTER_API_KEY == test_key
    
    def test_graphiti_llm_model_from_env(self, monkeypatch):
        """Test that Graphiti LLM model can be set via environment variable."""
        test_model = "openai/gpt-4"
        monkeypatch.setenv("GRAPHITI_LLM_MODEL", test_model)
        settings = Settings()
        
        assert settings.GRAPHITI_LLM_MODEL == test_model
    
    def test_graphiti_namespace_from_env(self, monkeypatch):
        """Test that Graphiti namespace can be set via environment variable."""
        test_namespace = "production_ad_retrieval"
        monkeypatch.setenv("GRAPHITI_NAMESPACE", test_namespace)
        settings = Settings()
        
        assert settings.GRAPHITI_NAMESPACE == test_namespace
    
    def test_all_graphiti_settings_from_env(self, monkeypatch):
        """Test that all Graphiti settings can be configured via environment variables."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "true")
        monkeypatch.setenv("GRAPHITI_NEO4J_URI", "bolt://custom:7687")
        monkeypatch.setenv("GRAPHITI_NEO4J_USER", "custom_user")
        monkeypatch.setenv("GRAPHITI_NEO4J_PASSWORD", "custom_pass")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
        monkeypatch.setenv("GRAPHITI_LLM_MODEL", "anthropic/claude-3-opus")
        monkeypatch.setenv("GRAPHITI_NAMESPACE", "test_namespace")
        
        settings = Settings()
        
        assert settings.GRAPHITI_ENABLED is True
        assert settings.GRAPHITI_NEO4J_URI == "bolt://custom:7687"
        assert settings.GRAPHITI_NEO4J_USER == "custom_user"
        assert settings.GRAPHITI_NEO4J_PASSWORD == "custom_pass"
        assert settings.OPENROUTER_API_KEY == "sk-test-key"
        assert settings.GRAPHITI_LLM_MODEL == "anthropic/claude-3-opus"
        assert settings.GRAPHITI_NAMESPACE == "test_namespace"


class TestExistingConfiguration:
    """Test that existing configuration still works."""
    
    def test_existing_settings_unchanged(self):
        """Test that existing settings are not affected by Graphiti additions."""
        settings = Settings()
        
        # Verify existing settings still work
        assert settings.DATA_DIR == "data"
        assert settings.CAMPAIGNS_PATH == "data/campaigns.jsonl"
        assert settings.EMBEDDINGS_PATH == "data/embeddings.npy"
        assert settings.FAISS_INDEX_PATH == "data/faiss.index"
        assert settings.BLOCKLIST_PATH == "data/blocklist.txt"
        assert settings.TAXONOMY_PATH == "data/taxonomy.json"
        assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
        assert settings.TOP_K_CANDIDATES == 1500
        assert settings.MAX_CAMPAIGNS_RETURNED == 1000
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
    
    def test_settings_can_be_instantiated_multiple_times(self):
        """Test that Settings can be instantiated multiple times."""
        settings1 = Settings()
        settings2 = Settings()
        
        assert settings1.GRAPHITI_ENABLED == settings2.GRAPHITI_ENABLED
        assert settings1.GRAPHITI_NEO4J_URI == settings2.GRAPHITI_NEO4J_URI

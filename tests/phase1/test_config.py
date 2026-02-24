"""Unit tests for configuration module."""

from src.core.config import Settings


def test_settings_defaults():
    """Test that settings have correct default values."""
    settings = Settings()

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


def test_settings_paths_are_strings():
    """Test that all path settings are strings."""
    settings = Settings()

    assert isinstance(settings.DATA_DIR, str)
    assert isinstance(settings.CAMPAIGNS_PATH, str)
    assert isinstance(settings.EMBEDDINGS_PATH, str)
    assert isinstance(settings.FAISS_INDEX_PATH, str)
    assert isinstance(settings.BLOCKLIST_PATH, str)
    assert isinstance(settings.TAXONOMY_PATH, str)


def test_settings_numeric_values():
    """Test that numeric settings have correct types and ranges."""
    settings = Settings()

    assert isinstance(settings.TOP_K_CANDIDATES, int)
    assert isinstance(settings.MAX_CAMPAIGNS_RETURNED, int)
    assert isinstance(settings.PORT, int)

    assert settings.TOP_K_CANDIDATES > 0
    assert settings.MAX_CAMPAIGNS_RETURNED > 0
    assert settings.PORT > 0
    assert settings.PORT < 65536


def test_settings_model_name():
    """Test that embedding model name is valid."""
    settings = Settings()

    assert isinstance(settings.EMBEDDING_MODEL, str)
    assert len(settings.EMBEDDING_MODEL) > 0
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"

"""Configuration settings for the Ad Retrieval System."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Paths
    DATA_DIR: str = "data"
    CAMPAIGNS_PATH: str = "data/campaigns.jsonl"
    EMBEDDINGS_PATH: str = "data/embeddings.npy"
    FAISS_INDEX_PATH: str = "data/faiss.index"
    BLOCKLIST_PATH: str = "data/blocklist.txt"
    TAXONOMY_PATH: str = "data/taxonomy.json"

    # Model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Search settings
    TOP_K_CANDIDATES: int = 1500
    MAX_CAMPAIGNS_RETURNED: int = 1000

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Graphiti settings
    GRAPHITI_ENABLED: bool = False
    GRAPHITI_NEO4J_URI: str = "bolt://localhost:7687"
    GRAPHITI_NEO4J_USER: str = "neo4j"
    GRAPHITI_NEO4J_PASSWORD: str = "password"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_VERIFY_SSL: bool = True  # Set False only to work around local cert issues (e.g. macOS)
    GRAPHITI_LLM_MODEL: str = "anthropic/claude-3.5-sonnet"
    GRAPHITI_NAMESPACE: str = "ad_retrieval"
    
    # Profile Analysis settings
    PROFILE_ANALYSIS_ENABLED: bool = True
    PROFILE_CACHE_SIZE: int = 10000
    PROFILE_CACHE_TTL_SECONDS: int = 604800  # 7 days
    PROFILE_ANALYSIS_TRIGGER_EVERY_N_QUERIES: int = 5
    PATTERN_RULES_PATH: str = "data/pattern_rules.json"
    PATTERN_CONFIDENCE_THRESHOLD: float = 0.75
    # Profile summary LLM (narrative + suggested campaigns); uses OpenRouter
    PROFILE_SUMMARY_LLM_MODEL: str = "openai/gpt-3.5-turbo"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

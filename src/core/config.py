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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

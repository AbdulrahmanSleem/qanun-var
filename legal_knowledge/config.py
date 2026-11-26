"""
Configuration settings for the QANUN-VAR Egyptian Legal Knowledge & Retrieval System.
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Project metadata
    PROJECT_NAME: str = "QANUN-VAR Legal Knowledge Engine"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    STORAGE_DIR: Path = BASE_DIR / "storage"

    # Embedding model configuration
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"  # "cpu", "cuda", "mps"
    EMBEDDING_DIMENSION: int = 1024  # BGE-M3 default dimension
    EMBEDDING_BATCH_SIZE: int = 16
    USE_FALLBACK_EMBEDDINGS: bool = True  # Set to False to load/download full BGE-M3 weights

    # Vector store configuration (Qdrant)
    VECTOR_STORE_BACKEND: Literal["qdrant"] = "qdrant"
    QDRANT_LOCATION: Optional[str] = ":memory:"  # ":memory:", local path, or None for remote
    QDRANT_URL: Optional[str] = None  # e.g., "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "egyptian_legal_articles"

    # BM25 Keyword Search configuration
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    BM25_EPSILON: float = 0.25

    # Hybrid Retrieval (RRF) configuration
    RRF_K: int = 60
    DENSE_SEARCH_WEIGHT: float = 0.6
    SPARSE_SEARCH_WEIGHT: float = 0.4
    DEFAULT_RETRIEVAL_TOP_K: int = 5
    MAX_RETRIEVAL_TOP_K: int = 50

    # Reranking configuration
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cpu"
    USE_RERANKER: bool = True
    USE_FALLBACK_RERANKER: bool = True  # Set to False to load full CrossEncoder weights
    RERANK_TOP_N: int = 10  # Number of candidates sent to reranker

    # Citation Verification configuration
    CITATION_MIN_LEXICAL_OVERLAP: float = 0.65  # Threshold for text quote authenticity
    CITATION_MIN_CONFIDENCE: float = 0.70

    # LLM configuration for Legal Q&A Agent
    LLM_PROVIDER: Literal["mock", "gemini", "openai", "anthropic", "ollama"] = "mock"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"
    LLM_TEMPERATURE: float = 0.0  # Zero temperature for deterministic legal adherence

    # Ingestion & Chunking configuration
    MAX_CHUNK_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

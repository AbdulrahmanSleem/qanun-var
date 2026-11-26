"""
Embedding services module.
"""

from legal_knowledge.embeddings.embedding_service import (
    BaseEmbeddingService,
    MultilingualEmbeddingService,
    FallbackDeterministicEmbedder,
)

__all__ = [
    "BaseEmbeddingService",
    "MultilingualEmbeddingService",
    "FallbackDeterministicEmbedder",
]

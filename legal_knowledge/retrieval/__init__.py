"""
Retrieval module exports.
"""

from legal_knowledge.retrieval.vector_store import QdrantVectorStore
from legal_knowledge.retrieval.semantic_search import SemanticSearchEngine
from legal_knowledge.retrieval.bm25_search import BM25SearchEngine
from legal_knowledge.retrieval.hybrid_search import HybridSearchEngine
from legal_knowledge.retrieval.reranker import MultilingualReranker
from legal_knowledge.retrieval.retrieval_service import (
    LegalRetrievalService,
    get_retrieval_service,
    search_legal_sources,
)

__all__ = [
    "QdrantVectorStore",
    "SemanticSearchEngine",
    "BM25SearchEngine",
    "HybridSearchEngine",
    "MultilingualReranker",
    "LegalRetrievalService",
    "get_retrieval_service",
    "search_legal_sources",
]

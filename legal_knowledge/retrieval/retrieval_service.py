"""
Unified Legal Retrieval Service for QANUN-VAR.
Exposes the shared asynchronous retrieval interface consumed by F1 (Legal Q&A),
F2 (Contract Review), and F3 (Case Analysis).
"""

from typing import List, Optional, Dict, Any
import time
import logging

from legal_knowledge.config import settings
from legal_knowledge.schemas.documents import LegalChunk
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.embeddings.embedding_service import MultilingualEmbeddingService
from legal_knowledge.retrieval.vector_store import QdrantVectorStore
from legal_knowledge.retrieval.semantic_search import SemanticSearchEngine
from legal_knowledge.retrieval.bm25_search import BM25SearchEngine
from legal_knowledge.retrieval.hybrid_search import HybridSearchEngine
from legal_knowledge.retrieval.reranker import MultilingualReranker

logger = logging.getLogger(__name__)


class LegalRetrievalService:
    """
    Central Legal Retrieval Engine providing dense, sparse, hybrid, and reranked
    search capabilities over authentic Egyptian legislation.
    """

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_service: Optional[MultilingualEmbeddingService] = None,
        bm25_search: Optional[BM25SearchEngine] = None,
        reranker: Optional[MultilingualReranker] = None,
    ):
        self.embedding_service = embedding_service or MultilingualEmbeddingService()
        self.vector_store = vector_store or QdrantVectorStore(
            vector_dim=self.embedding_service.dimension
        )
        self.bm25_search = bm25_search or BM25SearchEngine()
        self.reranker = reranker or MultilingualReranker()

        self.semantic_search = SemanticSearchEngine(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store
        )
        self.hybrid_search = HybridSearchEngine(
            semantic_search=self.semantic_search,
            bm25_search=self.bm25_search
        )

    def index_chunks(self, chunks: List[LegalChunk]) -> None:
        """
        Synchronously indexes chunks into both Qdrant vector store and BM25 index.
        Safe for updates: existing chunk IDs are replaced without duplicates.
        """
        if not chunks:
            return

        logger.info(f"Indexing {len(chunks)} legal chunks into vector store and BM25...")
        # 1. Compute embeddings for search text
        search_texts = [c.text_normalized for c in chunks]
        embeddings = self.embedding_service.embed_texts(search_texts)

        # 2. Upsert into Qdrant
        self.vector_store.upsert_chunks(chunks, embeddings)

        # 3. Add to BM25
        self.bm25_search.add_chunks(chunks)
        logger.info("Indexing completed successfully.")

    def delete_document(self, document_id: str) -> None:
        """Deletes all chunks belonging to a document from both vector store and BM25."""
        self.vector_store.delete_document(document_id)
        self.bm25_search.delete_document(document_id)
        logger.info(f"Document {document_id} removed from retrieval service.")

    async def search_legal_sources(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = settings.DEFAULT_RETRIEVAL_TOP_K,
        method: str = "hybrid",
        apply_reranking: bool = settings.USE_RERANKER
    ) -> List[RetrievedChunk]:
        """
        Core asynchronous retrieval contract for QANUN-VAR.
        
        Args:
            query: The legal query in Arabic or English.
            filters: Optional dictionary of metadata filters (e.g. {'law_number': '12', 'law_year': '2003'}).
            top_k: Number of retrieved articles to return.
            method: 'hybrid', 'dense', or 'sparse'.
            apply_reranking: Whether to apply cross-encoder reranking.
            
        Returns:
            List[RetrievedChunk] sorted by relevance score with original authentic text.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            return []

        # Enforce configurable boundary on top_k
        top_k = max(1, min(top_k, settings.MAX_RETRIEVAL_TOP_K))

        # Retrieve candidates based on chosen method
        if method == "dense":
            candidates = self.semantic_search.search(query=query, top_k=top_k * 2, filters=filters)
        elif method == "sparse":
            candidates = self.bm25_search.search(query=query, top_k=top_k * 2, filters=filters)
        else:
            # Default: Hybrid RRF
            candidates = self.hybrid_search.search(query=query, top_k=top_k * 2, filters=filters)

        # Apply reranking if requested
        if apply_reranking and candidates and self.reranker:
            final_results = self.reranker.rerank(query=query, chunks=candidates, top_n=top_k)
        else:
            final_results = candidates[:top_k]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.debug(f"Retrieved {len(final_results)} chunks for query in {elapsed_ms:.2f}ms")

        return final_results


# Module-level shared singleton for easy team import
_global_retrieval_service: Optional[LegalRetrievalService] = None


def get_retrieval_service() -> LegalRetrievalService:
    """Factory function providing singleton instance of LegalRetrievalService."""
    global _global_retrieval_service
    if _global_retrieval_service is None:
        _global_retrieval_service = LegalRetrievalService()
    return _global_retrieval_service


async def search_legal_sources(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5
) -> List[RetrievedChunk]:
    """
    Direct function interface matching team specification:
    async def search_legal_sources(query: str, filters: dict | None = None, top_k: int = 5) -> list[RetrievedChunk]
    """
    service = get_retrieval_service()
    return await service.search_legal_sources(query=query, filters=filters, top_k=top_k)

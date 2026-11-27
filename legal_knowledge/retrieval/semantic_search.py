"""
Dense Semantic Search Engine for Egyptian Legal Knowledge Base.
"""

from typing import List, Optional, Dict, Any
import logging
from legal_knowledge.embeddings.embedding_service import BaseEmbeddingService
from legal_knowledge.retrieval.vector_store import QdrantVectorStore
from legal_knowledge.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Performs semantic similarity search against indexed vector representations."""

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        vector_store: QdrantVectorStore
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """
        Embeds query and queries vector store for nearest legal articles.
        """
        if not query or not query.strip():
            return []

        # Generate dense vector for query
        query_vector = self.embedding_service.embed_query(query)

        # Query vector database
        results = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filters=filters
        )

        for res in results:
            res.retrieval_method = "dense"

        return results

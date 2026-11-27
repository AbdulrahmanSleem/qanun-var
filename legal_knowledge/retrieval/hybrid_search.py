"""
Hybrid Retrieval Engine combining Dense Semantic Search and Sparse BM25 using Reciprocal Rank Fusion (RRF).
"""

from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging

from legal_knowledge.config import settings
from legal_knowledge.retrieval.semantic_search import SemanticSearchEngine
from legal_knowledge.retrieval.bm25_search import BM25SearchEngine
from legal_knowledge.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    Executes simultaneous dense semantic and sparse BM25 retrieval,
    combining ranked lists using weighted Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        semantic_search: SemanticSearchEngine,
        bm25_search: BM25SearchEngine,
        rrf_k: int = settings.RRF_K,
        dense_weight: float = settings.DENSE_SEARCH_WEIGHT,
        sparse_weight: float = settings.SPARSE_SEARCH_WEIGHT
    ):
        self.semantic_search = semantic_search
        self.bm25_search = bm25_search
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        candidate_multiplier: int = 3
    ) -> List[RetrievedChunk]:
        """
        Executes hybrid search with RRF fusion.
        Retrieves candidate_multiplier * top_k from each retriever before fusion.
        """
        if not query.strip():
            return []

        fetch_k = max(top_k * candidate_multiplier, 10)

        # 1. Fetch dense candidates
        dense_results = self.semantic_search.search(
            query=query,
            top_k=fetch_k,
            filters=filters
        )

        # 2. Fetch sparse BM25 candidates
        sparse_results = self.bm25_search.search(
            query=query,
            top_k=fetch_k,
            filters=filters
        )

        # 3. Reciprocal Rank Fusion (RRF)
        fused_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, RetrievedChunk] = {}

        # Process dense ranks
        for rank, chunk in enumerate(dense_results, start=1):
            chunk_map[chunk.chunk_id] = chunk
            fused_scores[chunk.chunk_id] += self.dense_weight * (1.0 / (self.rrf_k + rank))

        # Process sparse ranks
        for rank, chunk in enumerate(sparse_results, start=1):
            if chunk.chunk_id not in chunk_map:
                chunk_map[chunk.chunk_id] = chunk
            fused_scores[chunk.chunk_id] += self.sparse_weight * (1.0 / (self.rrf_k + rank))

        # Sort descending by fused score
        sorted_chunk_ids = sorted(
            fused_scores.keys(),
            key=lambda cid: fused_scores[cid],
            reverse=True
        )

        final_chunks: List[RetrievedChunk] = []
        for cid in sorted_chunk_ids[:top_k]:
            base_chunk = chunk_map[cid]
            # Copy and assign fused score
            fused_chunk = base_chunk.model_copy()
            fused_chunk.score = float(fused_scores[cid])
            fused_chunk.retrieval_method = "hybrid_rrf"
            final_chunks.append(fused_chunk)

        logger.debug(
            f"Hybrid search fused {len(dense_results)} dense and {len(sparse_results)} sparse results "
            f"into {len(final_chunks)} final candidates."
        )
        return final_chunks

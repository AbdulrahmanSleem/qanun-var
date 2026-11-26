"""Hybrid retrieval: BGE-M3 dense + BM25 + bge-reranker-v2-m3.
All legal search in the project goes through retrieve_articles().

Owner: Ali
Implementation: delegates to legal_knowledge.retrieval.retrieval_service
which runs a full pipeline:
  1. BGE-M3 dense embedding search (Qdrant or in-memory)
  2. BM25 keyword search (rank-bm25)
  3. Reciprocal Rank Fusion of both lists
  4. Cross-encoder reranker (bge-reranker-v2-m3 or fallback alignment scorer)
"""
from __future__ import annotations

import asyncio
import logging
import sys
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Ensure legal_knowledge is importable when this file is used as a library
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


@dataclass
class RetrievedArticle:
    """A single retrieved legal article, ready for use by any agent."""
    law_name: str
    law_number: str
    article_number: str
    article_text: str
    score: float
    chapter: Optional[str] = None
    source_url: Optional[str] = None


def retrieve_articles(
    query: str,
    top_k: int = 10,
    rerank_top_n: int = 5,
    filters: Optional[dict] = None,
) -> list[RetrievedArticle]:
    """Main retrieval entry-point consumed by all agents.

    Args:
        query:        Legal question in Arabic or English.
        top_k:        Number of candidates fetched before reranking.
        rerank_top_n: Number of articles returned after reranking.
        filters:      Optional metadata filters, e.g.
                      {"law_number": "131", "law_year": "1948"}.

    Returns:
        List of RetrievedArticle ordered by descending relevance.
    """
    try:
        from legal_knowledge.retrieval.retrieval_service import get_retrieval_service

        service = get_retrieval_service()
        chunks = asyncio.run(
            service.search_legal_sources(query=query, filters=filters, top_k=top_k)
        )
        results: list[RetrievedArticle] = []
        for chunk in chunks[:rerank_top_n]:
            results.append(
                RetrievedArticle(
                    law_name=chunk.law_name or "",
                    law_number=chunk.law_number or "",
                    article_number=chunk.article_number or "",
                    article_text=chunk.text,
                    score=chunk.score,
                    chapter=chunk.chapter,
                    source_url=chunk.source_url,
                )
            )
        return results
    except Exception as exc:  # pragma: no cover
        logger.error("retrieve_articles failed: %s", exc, exc_info=True)
        raise

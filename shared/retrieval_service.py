
"""Hybrid retrieval: BGE-M3 dense + BM25 + bge-reranker-v2-m3.
All legal search in the project goes through retrieve_articles().
"""
from dataclasses import dataclass


@dataclass
class RetrievedArticle:
    law_name: str
    law_number: str
    article_number: str
    article_text: str
    score: float


def retrieve_articles(query: str, top_k: int = 10, rerank_top_n: int = 5) -> list[RetrievedArticle]:
    """TODO [Ali / Sleem]: Day 2-3 implementation.
    1. Embed query with BGE-M3 (dense) + BM25 over the article index.
    2. Reciprocal rank fusion of the two lists.
    3. Rerank fused top_k with bge-reranker-v2-m3 -> return top_n.
    """
    raise NotImplementedError("hybrid retrieval not implemented yet")

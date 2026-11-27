"""
Retrieval Metrics: Recall@K, Precision@K, MRR (Mean Reciprocal Rank), and Latency.
"""

from typing import List, Optional
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer


def is_match(retrieved_art: Optional[str], expected_art: Optional[str]) -> bool:
    """Normalize and compare retrieved article with target article."""
    if not retrieved_art or not expected_art:
        return False
    norm_r = ArabicNormalizer.normalize_article_number(retrieved_art)
    norm_e = ArabicNormalizer.normalize_article_number(expected_art)
    return norm_r == norm_e


def calculate_recall_at_k(retrieved_articles: List[str], expected_article: str, k: int) -> float:
    """
    Computes Recall@K: 1.0 if expected article is within top-k retrieved, else 0.0.
    """
    top_k_slice = retrieved_articles[:k]
    for art in top_k_slice:
        if is_match(art, expected_article):
            return 1.0
    return 0.0


def calculate_precision_at_k(retrieved_articles: List[str], expected_article: str, k: int) -> float:
    """
    Computes Precision@K: count of relevant articles / K.
    """
    if k <= 0:
        return 0.0
    top_k_slice = retrieved_articles[:k]
    hits = sum(1 for art in top_k_slice if is_match(art, expected_article))
    return hits / float(k)


def calculate_mrr(retrieved_articles: List[str], expected_article: str) -> float:
    """
    Computes Reciprocal Rank (1 / rank) for the first occurrence of expected article.
    """
    for rank, art in enumerate(retrieved_articles, start=1):
        if is_match(art, expected_article):
            return 1.0 / float(rank)
    return 0.0

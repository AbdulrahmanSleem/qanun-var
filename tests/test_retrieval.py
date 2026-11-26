"""
Tests for Dense, BM25, and Hybrid Retrieval with Metadata Filtering.
"""

import pytest
from legal_knowledge.retrieval.retrieval_service import LegalRetrievalService


@pytest.mark.asyncio
async def test_semantic_retrieval(test_retrieval_service: LegalRetrievalService):
    results = await test_retrieval_service.search_legal_sources(
        query="الالتزامات التعاقدية والظروف الطارئة",
        method="dense",
        top_k=2
    )
    assert len(results) > 0
    assert any(r.article_number == "147" for r in results)


@pytest.mark.asyncio
async def test_bm25_retrieval_exact_number(test_retrieval_service: LegalRetrievalService):
    # Query with exact article number
    results = await test_retrieval_service.search_legal_sources(
        query="مادة 31 مدة الاختبار في عقد العمل",
        method="sparse",
        top_k=2
    )
    assert len(results) > 0
    assert results[0].article_number == "31"


@pytest.mark.asyncio
async def test_hybrid_rrf_retrieval(test_retrieval_service: LegalRetrievalService):
    results = await test_retrieval_service.search_legal_sources(
        query="مدة الاختبار في عقد العمل الفردي",
        method="hybrid",
        top_k=2,
        apply_reranking=True
    )
    assert len(results) > 0
    assert results[0].article_number == "31"
    assert results[0].law_number == "12"


@pytest.mark.asyncio
async def test_metadata_filtering(test_retrieval_service: LegalRetrievalService):
    # Filter strictly for Civil Code (Law 131)
    results = await test_retrieval_service.search_legal_sources(
        query="عقد",
        filters={"law_number": "131"},
        top_k=5
    )
    assert len(results) > 0
    for r in results:
        assert r.law_number == "131"
        assert r.article_number != "31"  # Labor law article must be filtered out

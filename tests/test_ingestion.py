"""
Tests for Document Loaders, Ingestion Pipeline, and Deduplication.
"""

from pathlib import Path
import pytest
from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline
from legal_knowledge.retrieval.retrieval_service import LegalRetrievalService


@pytest.mark.asyncio
async def test_end_to_end_ingestion(tmp_path: Path):
    sample_law_content = (
        "الجريدة الرسمية - العدد 1 بتاريخ 01/01/2020\n"
        "قانون رقم 50 لسنة 2020 بإصدار قانون حماية المستهلك\n"
        "الحالة القانونية: سارٍ\n\n"
        "الباب الأول: أحكام عامة\n\n"
        "مادة 1:\n"
        "المستهلك هو كل شخص طبيعي يشتري سلعة أو يستفيد من خدمة.\n\n"
        "مادة 2:\n"
        "يلتزم المورد بقواعد الأمانة والشفافية مع المستهلك."
    )
    test_file = tmp_path / "consumer_protection.txt"
    test_file.write_text(sample_law_content, encoding="utf-8")

    retrieval_service = LegalRetrievalService()
    pipeline = LegalIngestionPipeline(retrieval_service=retrieval_service)

    doc, chunks = pipeline.ingest_file(test_file)

    assert doc.law_number == "50"
    assert doc.law_year == "2020"
    assert doc.legal_status == "in_force"
    # Document contains preamble header + 2 legal articles
    assert len(chunks) >= 2
    assert any(c.article_number == "1" for c in chunks)
    assert any(c.article_number == "2" for c in chunks)

    # Verify search finds the newly ingested article
    results = await retrieval_service.search_legal_sources("من هو المستهلك قانوناً؟", top_k=2)
    assert len(results) > 0
    assert results[0].article_number == "1"


@pytest.mark.asyncio
async def test_deduplication_and_update(tmp_path: Path):
    initial_content = (
        "قانون رقم 99 لسنة 2021\n"
        "مادة 1:\n"
        "النص الأولي للمادة الأولى."
    )
    test_file = tmp_path / "test_law.txt"
    test_file.write_text(initial_content, encoding="utf-8")

    retrieval_service = LegalRetrievalService()
    pipeline = LegalIngestionPipeline(retrieval_service=retrieval_service)

    # Ingest version 1
    doc1, chunks1 = pipeline.ingest_file(test_file)
    assert any(c.article_number == "1" for c in chunks1)
    art1_chunk = next(c for c in chunks1 if c.article_number == "1")
    assert "الأولي" in art1_chunk.text

    # Update file with amendment
    updated_content = (
        "قانون رقم 99 لسنة 2021\n"
        "مادة 1:\n"
        "النص المعدل للمادة الأولى مع شروط إضافية."
    )
    test_file.write_text(updated_content, encoding="utf-8")

    # Ingest version 2
    doc2, chunks2 = pipeline.ingest_file(test_file)
    assert doc1.document_id == doc2.document_id
    assert any(c.article_number == "1" for c in chunks2)
    art1_updated = next(c for c in chunks2 if c.article_number == "1")
    assert "المعدل" in art1_updated.text

    # Verify vector store contains updated chunk and NO duplicate
    results = await retrieval_service.search_legal_sources("النص المعدل", top_k=5)
    matching = [r for r in results if r.document_id == doc1.document_id and r.article_number == "1"]
    assert len(matching) == 1
    assert "المعدل" in matching[0].text

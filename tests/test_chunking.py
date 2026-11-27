"""
Tests for Legal Structure Parser and Article-Level Chunker.
"""

from legal_knowledge.ingestion.legal_parser import LegalStructureParser
from legal_knowledge.ingestion.chunker import LegalArticleChunker
from legal_knowledge.schemas.documents import LegalDocument


def test_legal_structure_parser():
    sample_text = (
        "الكتاب الأول: الالتزامات\n"
        "الباب الأول: مصادر الالتزام\n"
        "الفصل الأول: العقد\n"
        "مادة 147:\n"
        "العقد شريعة المتعاقدين.\n\n"
        "مادة 148:\n"
        "يجب تنفيذ العقد بحسن نية."
    )
    articles = LegalStructureParser.parse_articles(sample_text)
    substantive_articles = [a for a in articles if a.article_number != "ديباجة"]
    assert len(substantive_articles) == 2
    assert substantive_articles[0].article_number == "147"
    assert "العقد شريعة المتعاقدين" in substantive_articles[0].original_text
    assert substantive_articles[0].chapter == "الباب الأول: مصادر الالتزام"
    assert substantive_articles[0].section == "الفصل الأول: العقد"

    assert substantive_articles[1].article_number == "148"
    assert "حسن نية" in substantive_articles[1].original_text


def test_article_level_chunker():
    doc = LegalDocument(
        document_id="doc_123",
        title="قانون تجريبي",
        law_name="القانون التجريبي رقم 1 لسنة 2024",
        law_number="1",
        law_year="2024"
    )
    sample_text = (
        "مادة 1:\n"
        "تسري أحكام هذا القانون على كافة النزاعات.\n\n"
        "مادة 2:\n"
        "ينشر هذا القانون في الجريدة الرسمية."
    )
    parsed = LegalStructureParser.parse_articles(sample_text)
    chunker = LegalArticleChunker(max_tokens=500)
    chunks = chunker.chunk_document(doc, parsed)

    assert len(chunks) == 2
    assert chunks[0].chunk_id == "doc_123_art_1_0"
    assert chunks[0].article_number == "1"
    assert chunks[0].law_name == "القانون التجريبي رقم 1 لسنة 2024"
    assert chunks[0].text != ""
    assert chunks[0].text_normalized != ""


def test_oversized_article_chunker():
    doc = LegalDocument(
        document_id="doc_long",
        title="قانون طويل",
        law_name="قانون طويل"
    )
    long_article_body = "فقرة تجريبية طويلة تتضمن العديد من البنود التفصيلية والقواعد القانونية الإجرائية.\n" * 40
    sample_text = f"مادة 10:\n{long_article_body}"

    parsed = LegalStructureParser.parse_articles(sample_text)
    chunker = LegalArticleChunker(max_tokens=100)
    chunks = chunker.chunk_document(doc, parsed)

    assert len(chunks) > 1
    # Check that context header is preserved in all sub-chunks
    for c in chunks:
        assert "مادة 10" in c.text

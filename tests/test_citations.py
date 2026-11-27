"""
Tests for Citation Verification Engine.
"""

from legal_knowledge.citations.citation_verifier import CitationVerifier
from legal_knowledge.schemas.citations import Citation
from legal_knowledge.schemas.retrieval import RetrievedChunk


def test_valid_citation_verification(citation_verifier: CitationVerifier):
    official_text = (
        "العقد شريعة المتعاقدين، فلا يجوز نقضه ولا تعديله إلا باتفاق الطرفين، أو للأسباب التي يقررها القانون."
    )
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk_147",
            text=official_text,
            law_name="القانون المدني رقم 131 لسنة 1948",
            law_number="131",
            law_year="1948",
            article_number="147"
        )
    ]

    valid_citation = Citation(
        law_name="القانون المدني المصري",
        law_number="131",
        article_number="147",
        quoted_text="العقد شريعة المتعاقدين، فلا يجوز نقضه ولا تعديله إلا باتفاق الطرفين",
        claim_text="لا يجوز تعديل العقد بإرادة منفردة"
    )

    report = citation_verifier.verify_citation(valid_citation, retrieved)
    assert report.is_valid is True
    assert report.law_matched is True
    assert report.article_matched is True
    assert report.quote_verified is True
    assert report.quote_similarity >= 0.8
    assert len(report.warnings) == 0


def test_hallucinated_law_detection(citation_verifier: CitationVerifier):
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk_147",
            text="العقد شريعة المتعاقدين...",
            law_name="القانون المدني",
            article_number="147"
        )
    ]

    fake_citation = Citation(
        law_name="قانون التجارة البحرية والجمارك الفضائية",
        law_number="999",
        article_number="147",
        quoted_text="نص قانوني غير موجود بالمرة"
    )

    report = citation_verifier.verify_citation(fake_citation, retrieved)
    assert report.is_valid is False
    assert report.law_matched is False
    assert any("غير موجود" in w for w in report.warnings)


def test_mismatched_article_number(citation_verifier: CitationVerifier):
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk_147",
            text="العقد شريعة المتعاقدين...",
            law_name="القانون المدني",
            article_number="147"
        )
    ]

    wrong_art_citation = Citation(
        law_name="القانون المدني",
        article_number="999",  # Non-existent article in retrieved set
        quoted_text="العقد شريعة المتعاقدين"
    )

    report = citation_verifier.verify_citation(wrong_art_citation, retrieved)
    assert report.is_valid is False
    assert report.article_matched is False
    assert any("رقم المادة" in w for w in report.warnings)


def test_corrupted_quotation_detection(citation_verifier: CitationVerifier):
    official_text = "تحدد مدة الاختبار في عقد العمل بما لا يجاوز ثلاثة أشهر."
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk_31",
            text=official_text,
            law_name="قانون العمل",
            article_number="31"
        )
    ]

    # Fabricated quote altering legal meaning
    corrupted_quote_citation = Citation(
        law_name="قانون العمل",
        article_number="31",
        quoted_text="يجوز لصاحب العمل مد فترة الاختبار إلى سنة كاملة دون قيود."
    )

    report = citation_verifier.verify_citation(corrupted_quote_citation, retrieved)
    assert report.is_valid is False
    assert report.quote_verified is False
    assert any("النص المقتبس لا يتطابق" in w for w in report.warnings)

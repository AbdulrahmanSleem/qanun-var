"""
Tests for Multilingual Cross-Encoder & Fallback Alignment Reranker.
"""

from legal_knowledge.retrieval.reranker import MultilingualReranker, FallbackArabicReranker
from legal_knowledge.schemas.retrieval import RetrievedChunk


def test_fallback_arabic_reranker_scoring():
    query = "أقصى مدة لفترة الاختبار في عقد العمل"
    doc_match = "تحدد مدة الاختبار في عقد العمل الفردي ولا يجوز أن تزيد عن ثلاثة أشهر."
    doc_irrelevant = "تسري النصوص التشريعية على جميع المسائل في لفظها وفحواها."

    score_match = FallbackArabicReranker.score_pair(
        query=query,
        document_text=doc_match,
        law_name="قانون العمل",
        article_num="31"
    )

    score_irrelevant = FallbackArabicReranker.score_pair(
        query=query,
        document_text=doc_irrelevant,
        law_name="القانون المدني",
        article_num="1"
    )

    assert score_match > score_irrelevant
    assert score_match > 0.3


def test_multilingual_reranker_reordering():
    reranker = MultilingualReranker(use_fallback=True)

    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            text="تسري النصوص التشريعية على جميع المسائل في لفظها وفحواها.",
            law_name="القانون المدني",
            article_number="1",
            score=0.9  # Initially high but irrelevant
        ),
        RetrievedChunk(
            chunk_id="c2",
            text="تحدد مدة الاختبار في عقد العمل الفردي ولا يجوز بأكثر من ثلاثة أشهر.",
            law_name="قانون العمل",
            article_number="31",
            score=0.4  # Initially lower
        )
    ]

    reranked = reranker.rerank(
        query="ما هي مدة الاختبار في عقد العمل؟",
        chunks=chunks,
        top_n=2
    )

    assert len(reranked) == 2
    # Chunk c2 (article 31) must be promoted to rank 1
    assert reranked[0].chunk_id == "c2"
    assert reranked[0].article_number == "31"

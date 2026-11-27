"""
Pytest fixtures for QANUN-VAR Legal Knowledge module tests.
"""

import sys
from pathlib import Path
import pytest

# Ensure root package is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from legal_knowledge.config import settings
from legal_knowledge.schemas.documents import LegalDocument, LegalChunk
from legal_knowledge.retrieval.retrieval_service import LegalRetrievalService
from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline
from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
from legal_knowledge.citations.citation_verifier import CitationVerifier


@pytest.fixture
def sample_civil_article_raw() -> str:
    return (
        "مادة 147:\n"
        "(1) العقد شريعة المتعاقدين، فلا يجوز نقضه ولا تعديله إلا باتفاق الطرفين، أو للأسباب التي يقررها القانون.\n"
        "(2) ومع ذلك إذا طرأت حوادث استثنائية عامة غير متوقعة وترتب على حدوثها أن تنفيذ الالتزام التعاقدي صار يرهق المدين، "
        "جاز للقاضي رد الالتزام المرهق إلى الحد المعقول."
    )


@pytest.fixture
def sample_labor_article_raw() -> str:
    return (
        "مادة 31:\n"
        "تحدد مدة الاختبار في عقد العمل الفردي، ولا يجوز تحديد مدة الاختبار في عقد العمل بأكثر من ثلاثة أشهر، "
        "ولا يجوز تعيين العامل تحت الاختبار أكثر من مرة واحدة عند صاحب عمل واحد."
    )


@pytest.fixture
def sample_legal_document() -> LegalDocument:
    return LegalDocument(
        document_id="test_civil_131_1948",
        title="القانون المدني المصري",
        law_name="القانون المدني رقم 131 لسنة 1948",
        law_number="131",
        law_year="1948",
        source_url="https://manshurat.org/node/14844",
        publication_date="1948-07-29",
        legal_status="in_force"
    )


@pytest.fixture
def sample_chunks(sample_civil_article_raw, sample_labor_article_raw) -> list[LegalChunk]:
    return [
        LegalChunk(
            chunk_id="chunk_civil_147",
            document_id="test_civil_131_1948",
            text=sample_civil_article_raw,
            text_normalized="ماده 147 العقد شريعه المتعاقدين فلا يجوز نقضه ولا تعديله الا باتفاق الطرفين",
            law_name="القانون المدني رقم 131 لسنة 1948",
            law_number="131",
            law_year="1948",
            article_number="147",
            chapter="الباب الأول",
            section="الفصل الأول",
            legal_status="in_force"
        ),
        LegalChunk(
            chunk_id="chunk_labor_31",
            document_id="test_labor_12_2003",
            text=sample_labor_article_raw,
            text_normalized="ماده 31 تحدد مده الاختبار في عقد العمل الفردي ولا يجوز تحديد مده الاختبار باكثر من ثلاثه اشهر",
            law_name="قانون العمل رقم 12 لسنة 2003",
            law_number="12",
            law_year="2003",
            article_number="31",
            chapter="الكتاب الثاني",
            section="الباب الأول",
            legal_status="in_force"
        )
    ]


@pytest.fixture
def test_retrieval_service(sample_chunks) -> LegalRetrievalService:
    service = LegalRetrievalService()
    service.index_chunks(sample_chunks)
    return service


@pytest.fixture
def test_qa_agent(test_retrieval_service) -> LegalQAAgent:
    return LegalQAAgent(retrieval_service=test_retrieval_service)


@pytest.fixture
def citation_verifier() -> CitationVerifier:
    return CitationVerifier()

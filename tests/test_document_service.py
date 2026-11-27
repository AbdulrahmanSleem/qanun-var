from pathlib import Path

import pymupdf
import pytest
from docx import Document

from shared.document_service import extract


def test_extract_txt_contract(tmp_path: Path) -> None:
    contract = tmp_path / "employment.txt"
    contract.write_text(
        "عقد عمل\nالمادة الأولى: يلتزم العامل بتنفيذ العمل.",
        encoding="utf-8",
    )

    result = extract(str(contract))

    assert result.source_format == "txt"
    assert "عقد عمل" in result.text
    assert result.ocr_used is False
    assert result.needs_human_confirmation is False


def test_extract_docx_contract_with_table(tmp_path: Path) -> None:
    contract = tmp_path / "service.docx"
    document = Document()
    document.add_paragraph("عقد خدمات")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "الطرف الأول"
    table.rows[0].cells[1].text = "شركة الاختبار"
    document.save(contract)

    result = extract(str(contract))

    assert result.source_format == "docx"
    assert "عقد خدمات" in result.text
    assert "الطرف الأول | شركة الاختبار" in result.text


def test_extract_pdf_contract(tmp_path: Path) -> None:
    contract = tmp_path / "nda.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "TEST NDA contract")
    document.save(contract)
    document.close()

    result = extract(str(contract))

    assert result.source_format == "pdf"
    assert "TEST NDA" in result.text


def test_extract_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Document not found"):
        extract(str(tmp_path / "missing.pdf"))


def test_extract_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a file"):
        extract(str(tmp_path))


def test_extract_rejects_unsupported_format(tmp_path: Path) -> None:
    contract = tmp_path / "contract.rtf"
    contract.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported format"):
        extract(str(contract))

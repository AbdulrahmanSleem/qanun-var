
"""Shared document ingestion for PDF, DOCX, and TXT files.

Every agent that reads files imports from this module.
M-01 supports digital-text extraction only.
OCR and human confirmation belong to M-02.
"""
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from docx import Document


@dataclass
class ExtractedDocument:
    text: str
    source_format: str  # "pdf" | "docx" | "image" | "txt"
    ocr_used: bool = False
    needs_human_confirmation: bool = False


def extract(path: str) -> ExtractedDocument:
    """Extract digital text from PDF, DOCX, or TXT files."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        source_format = "pdf"
        try:
            with pymupdf.open(file_path) as pdf:
                text = "\n".join(
                    page.get_text("text") for page in pdf
                ).strip()
        except Exception as exc:
            raise RuntimeError(
                f"Could not read PDF document: {exc}"
            ) from exc
        if not text:
            raise ValueError(
                "No digital text found. This may be a scanned PDF. "
                "OCR will be implemented in M-02."
            )

    elif extension == ".docx":
        source_format = "docx"
        try:
            document = Document(file_path)
            parts = [paragraph.text for paragraph in document.paragraphs]
            for table in document.tables:
                for row in table.rows:
                    parts.append(
                        " | ".join(cell.text for cell in row.cells)
                    )
            text = "\n".join(
                part for part in parts if part.strip()
            ).strip()
        except Exception as exc:
            raise RuntimeError(
                f"Could not read DOCX document: {exc}"
            ) from exc
        if not text:
            raise ValueError(
                "The DOCX document contains no extractable text."
            )

    elif extension == ".txt":
        source_format = "txt"
        try:
            try:
                text = file_path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                text = file_path.read_text(encoding="cp1256")
            text = text.strip()
        except Exception as exc:
            raise RuntimeError(
                f"Could not read TXT document: {exc}"
            ) from exc
        if not text:
            raise ValueError("The TXT document is empty.")

    else:
        raise ValueError(
            f"Unsupported format '{extension}'. "
            "Supported formats: PDF, DOCX, TXT."
        )

    return ExtractedDocument(
        text=text,
        source_format=source_format,
        ocr_used=False,
        needs_human_confirmation=False,
    )


def confirm_text(doc_id: str, corrected_text: str) -> None:
    """Preserve the shared interface. Implementation belongs to M-02."""
    raise NotImplementedError(
        "Text confirmation storage will be implemented in M-02."
    )

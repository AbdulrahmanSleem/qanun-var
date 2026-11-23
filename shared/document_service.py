
"""Shared document ingestion: PDF/DOCX/Images + Arabic OCR.
Every agent that reads files imports from here — never parse files directly.
IMPORTANT (MVP guardrail): for scanned documents the extracted text must be
shown to the user for confirmation BEFORE analysis (human-in-the-loop).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractedDocument:
    text: str
    source_format: str            # "pdf" | "docx" | "image" | "txt"
    ocr_used: bool = False
    needs_human_confirmation: bool = False


def extract(path: str) -> ExtractedDocument:
    """TODO [Mo3taz]: PyMuPDF/python-docx for digital files;
    Tesseract(ara)/EasyOCR for scans, setting needs_human_confirmation=True."""
    raise NotImplementedError("document extraction not implemented yet")


def confirm_text(doc_id: str, corrected_text: str) -> None:
    """Store the user-confirmed OCR text so agents never analyze unconfirmed text."""
    raise NotImplementedError

"""Ingestion pipeline adapter for QANUN-VAR legal knowledge base.

Owner: Ali
Provides programmatic ingestion of Egyptian legal documents (PDF, DOCX, TXT)
into the vector store and BM25 index.
"""
from __future__ import annotations

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline


def get_pipeline() -> LegalIngestionPipeline:
    """Get configured legal document ingestion pipeline."""
    return LegalIngestionPipeline()


def ingest_document(file_path: str):
    """Ingest a single document into the legal knowledge base."""
    pipeline = get_pipeline()
    return pipeline.ingest_file(file_path)

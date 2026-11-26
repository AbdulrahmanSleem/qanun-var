"""
Ingestion module exports.
"""

from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer
from legal_knowledge.ingestion.loaders import DocumentLoader, DocumentLoaderError
from legal_knowledge.ingestion.legal_parser import LegalStructureParser, ParsedArticle
from legal_knowledge.ingestion.metadata_extractor import LegalMetadataExtractor
from legal_knowledge.ingestion.chunker import LegalArticleChunker
from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline

__all__ = [
    "ArabicNormalizer",
    "DocumentLoader",
    "DocumentLoaderError",
    "LegalStructureParser",
    "ParsedArticle",
    "LegalMetadataExtractor",
    "LegalArticleChunker",
    "LegalIngestionPipeline",
]

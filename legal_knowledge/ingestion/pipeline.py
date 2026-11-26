"""
End-to-End Legal Ingestion Pipeline for Egyptian Legislation.
Executes document loading, text extraction, normalization, structure parsing,
article chunking, metadata extraction, embedding generation, and vector indexing.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import hashlib

from legal_knowledge.schemas.documents import LegalDocument, LegalChunk
from legal_knowledge.ingestion.loaders import DocumentLoader
from legal_knowledge.ingestion.metadata_extractor import LegalMetadataExtractor
from legal_knowledge.ingestion.legal_parser import LegalStructureParser
from legal_knowledge.ingestion.chunker import LegalArticleChunker

logger = logging.getLogger(__name__)


class LegalIngestionPipeline:
    """
    Orchestrates the 9-stage legal ingestion pipeline for PDF, DOCX, and TXT legislation.
    """

    def __init__(
        self,
        retrieval_service: Optional[Any] = None,
        chunker: Optional[LegalArticleChunker] = None
    ):
        if retrieval_service is None:
            from legal_knowledge.retrieval.retrieval_service import get_retrieval_service
            self.retrieval_service = get_retrieval_service()
        else:
            self.retrieval_service = retrieval_service
        self.chunker = chunker or LegalArticleChunker()
        # Track ingested document hashes to avoid redundant re-indexing
        self._document_registry: Dict[str, str] = {}

    def ingest_file(
        self,
        file_path: str | Path,
        source_url: Optional[str] = None,
        provided_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[LegalDocument, List[LegalChunk]]:
        """
        Ingests a legal document file (.pdf, .docx, .txt).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Legal document file not found: {path}")

        logger.info(f"[Ingestion Stage 1 & 2] Loading and extracting text from: {path.name}")
        raw_text = DocumentLoader.load(path)

        return self.ingest_raw_text(
            text=raw_text,
            filename=path.name,
            source_url=source_url,
            provided_metadata=provided_metadata,
            file_path=str(path.resolve())
        )

    def ingest_raw_text(
        self,
        text: str,
        filename: Optional[str] = None,
        source_url: Optional[str] = None,
        provided_metadata: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None
    ) -> Tuple[LegalDocument, List[LegalChunk]]:
        """
        Ingests legal text through the complete 9-stage pipeline.
        """
        if not text or not text.strip():
            raise ValueError("Cannot ingest empty legal text.")

        # Stage 3, 4, 7: Metadata extraction and preliminary cleaning
        logger.info("[Ingestion Stage 3 & 7] Extracting verifiable metadata...")
        meta = LegalMetadataExtractor.extract_document_metadata(
            text=text,
            filename=filename,
            source_url=source_url,
            provided_metadata=provided_metadata
        )

        doc_id = LegalMetadataExtractor.generate_document_id(
            law_name=meta["law_name"],
            law_number=meta["law_number"],
            law_year=meta["law_year"]
        )

        # Check document hash for changes
        doc_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if self._document_registry.get(doc_id) == doc_hash:
            logger.info(f"Document {doc_id} has not changed. Skipping redundant re-indexing.")

        # If document already exists with different content, clear previous chunks
        self.retrieval_service.delete_document(doc_id)

        doc_title = meta.get("law_name") or filename or "تشريع مصري"
        document = LegalDocument(
            document_id=doc_id,
            title=doc_title,
            law_name=meta["law_name"],
            law_number=meta["law_number"],
            law_year=meta["law_year"],
            source_url=meta["source_url"],
            publication_date=meta["publication_date"],
            amendment_date=meta["amendment_date"],
            legal_status=meta["legal_status"],
            raw_text=text,
            file_path=file_path,
            metadata=meta
        )

        # Stage 5: Legal structure detection
        logger.info("[Ingestion Stage 5] Parsing legal structure (Books, Chapters, Articles)...")
        parsed_articles = LegalStructureParser.parse_articles(text)

        # Stage 6: Article-level chunking
        logger.info("[Ingestion Stage 6] Generating article-level chunks with dual text representations...")
        chunks = self.chunker.chunk_document(document, parsed_articles)

        # Stage 8 & 9: Embedding generation and Vector database indexing
        logger.info(f"[Ingestion Stage 8 & 9] Generating embeddings and indexing {len(chunks)} chunks...")
        self.retrieval_service.index_chunks(chunks)

        self._document_registry[doc_id] = doc_hash
        logger.info(f"Successfully completed ingestion for: {document.law_name} ({len(chunks)} articles)")

        return document, chunks

    def ingest_directory(
        self,
        directory_path: str | Path,
        recursive: bool = False
    ) -> List[Tuple[LegalDocument, List[LegalChunk]]]:
        """Ingest all supported legal documents in a directory."""
        dir_p = Path(directory_path)
        if not dir_p.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_p}")

        extensions = ["*.txt", "*.docx", "*.pdf"]
        files = []
        for ext in extensions:
            if recursive:
                files.extend(dir_p.rglob(ext))
            else:
                files.extend(dir_p.glob(ext))

        results = []
        for file in files:
            try:
                res = self.ingest_file(file)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to ingest file {file.name}: {e}")

        return results

    def delete_document(self, document_id: str) -> None:
        """Deletes a document from the system."""
        self.retrieval_service.delete_document(document_id)
        if document_id in self._document_registry:
            del self._document_registry[document_id]
        logger.info(f"Deleted document {document_id}")

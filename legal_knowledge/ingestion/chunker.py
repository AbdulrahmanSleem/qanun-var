"""
Article-Level Legal Chunker.

Chunks legislation strictly by legal article ('مادة'), ensuring legal provisions
are not randomly fractured across token boundaries while maintaining contextual
headers for oversized articles.
"""

from typing import List
import logging
from legal_knowledge.config import settings
from legal_knowledge.schemas.documents import LegalChunk, LegalDocument
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer
from legal_knowledge.ingestion.legal_parser import ParsedArticle, LegalStructureParser
from legal_knowledge.ingestion.metadata_extractor import LegalMetadataExtractor

logger = logging.getLogger(__name__)


class LegalArticleChunker:
    """Article-level chunker adhering to Egyptian legal structure."""

    def __init__(self, max_tokens: int = settings.MAX_CHUNK_TOKENS, overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Approximate token count for Arabic text (approx 1 token ~= 4 characters / 0.75 words)."""
        words = text.split()
        return int(len(words) * 1.3)

    def chunk_document(self, document: LegalDocument, parsed_articles: List[ParsedArticle]) -> List[LegalChunk]:
        """
        Transforms parsed legal articles into searchable, quote-safe LegalChunks.
        """
        chunks: List[LegalChunk] = []
        chunk_counter = 0

        for article in parsed_articles:
            raw_text = article.original_text.strip()
            if not raw_text:
                continue

            est_tokens = self.estimate_tokens(raw_text)

            if est_tokens <= self.max_tokens:
                # Normal article: 1 chunk
                chunk_id = LegalMetadataExtractor.generate_chunk_id(
                    document.document_id,
                    article.article_number,
                    sub_index=0
                )
                original_text, normalized_text = ArabicNormalizer.process_text_pair(raw_text)

                chunk = LegalChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=original_text,
                    text_normalized=normalized_text,
                    law_name=document.law_name,
                    law_number=document.law_number,
                    law_year=document.law_year,
                    article_number=article.article_number,
                    chapter=article.chapter,
                    section=article.section,
                    source_url=document.source_url,
                    publication_date=document.publication_date,
                    amendment_date=document.amendment_date,
                    legal_status=document.legal_status,
                    chunk_index=chunk_counter,
                    token_count=est_tokens
                )
                chunks.append(chunk)
                chunk_counter += 1
            else:
                # Oversized article: split by paragraphs / numbered clauses
                sub_chunks = self._split_long_article(
                    article=article,
                    document=document,
                    start_index=chunk_counter
                )
                chunks.extend(sub_chunks)
                chunk_counter += len(sub_chunks)

        logger.info(f"Generated {len(chunks)} legal chunks from document '{document.law_name}'.")
        return chunks

    def _split_long_article(
        self,
        article: ParsedArticle,
        document: LegalDocument,
        start_index: int
    ) -> List[LegalChunk]:
        """Splits an oversized legal article at paragraph/item boundaries, prepending context."""
        paragraphs = [p.strip() for p in article.original_text.splitlines() if p.strip()]
        sub_chunks: List[LegalChunk] = []

        current_paras: List[str] = []
        current_tokens = 0
        sub_idx = 0

        header_prefix = f"[{document.law_name} - مادة {article.article_number}]\n"

        for p in paragraphs:
            p_tokens = self.estimate_tokens(p)
            if current_tokens + p_tokens > self.max_tokens and current_paras:
                # Flush current batch
                sub_text = header_prefix + "\n".join(current_paras)
                orig_text, norm_text = ArabicNormalizer.process_text_pair(sub_text)

                chunk_id = LegalMetadataExtractor.generate_chunk_id(
                    document.document_id,
                    article.article_number,
                    sub_index=sub_idx
                )
                sub_chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        text=orig_text,
                        text_normalized=norm_text,
                        law_name=document.law_name,
                        law_number=document.law_number,
                        law_year=document.law_year,
                        article_number=article.article_number,
                        chapter=article.chapter,
                        section=article.section,
                        source_url=document.source_url,
                        publication_date=document.publication_date,
                        amendment_date=document.amendment_date,
                        legal_status=document.legal_status,
                        chunk_index=start_index + sub_idx,
                        token_count=current_tokens
                    )
                )
                sub_idx += 1
                current_paras = [p]
                current_tokens = p_tokens
            else:
                current_paras.append(p)
                current_tokens += p_tokens

        if current_paras:
            sub_text = header_prefix + "\n".join(current_paras)
            orig_text, norm_text = ArabicNormalizer.process_text_pair(sub_text)
            chunk_id = LegalMetadataExtractor.generate_chunk_id(
                document.document_id,
                article.article_number,
                sub_index=sub_idx
            )
            sub_chunks.append(
                LegalChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=orig_text,
                    text_normalized=norm_text,
                    law_name=document.law_name,
                    law_number=document.law_number,
                    law_year=document.law_year,
                    article_number=article.article_number,
                    chapter=article.chapter,
                    section=article.section,
                    source_url=document.source_url,
                    publication_date=document.publication_date,
                    amendment_date=document.amendment_date,
                    legal_status=document.legal_status,
                    chunk_index=start_index + sub_idx,
                    token_count=current_tokens
                )
            )

        return sub_chunks

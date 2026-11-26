"""
BM25 Keyword Search Engine for Egyptian Legal Terminology and Article Numbers.
"""

import math
from collections import Counter
from typing import List, Optional, Dict, Any
import logging

from legal_knowledge.config import settings
from legal_knowledge.schemas.documents import LegalChunk
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class BM25SearchEngine:
    """
    Robust Lucene-standard BM25 search engine tailored for Arabic legal phrases,
    exact article numbers, and legislative codes.
    Guarantees non-negative IDFs across collections of any size (even N=1 or N=2).
    """

    def __init__(
        self,
        k1: float = settings.BM25_K1,
        b: float = settings.BM25_B,
        epsilon: float = settings.BM25_EPSILON
    ):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.chunks: List[LegalChunk] = []
        self.corpus_tokens: List[List[str]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """
        Tokenize Arabic legal text using normalized representation.
        Extracts words, digits, and root/clitic stripped sub-tokens (e.g., 'والخطأ' -> ['والخطأ', 'الخطأ', 'خطأ']).
        """
        if not text:
            return []
        norm = ArabicNormalizer.normalize_for_search(text)
        raw_tokens = norm.split()
        
        tokens: List[str] = []
        for tok in raw_tokens:
            tokens.append(tok)
            # Clitic stripping for prefixes: و, ف, ك, ب, ل
            stripped = tok
            if len(stripped) >= 4 and stripped[0] in ['و', 'ف', 'ب', 'ل', 'ك']:
                stem1 = stripped[1:]
                tokens.append(stem1)
                stripped = stem1

            # Strip definite article: ال
            if len(stripped) >= 4 and stripped.startswith("ال"):
                stem2 = stripped[2:]
                tokens.append(stem2)

        return tokens

    def index_chunks(self, chunks: List[LegalChunk]) -> None:
        """Indexes or re-indexes legal chunks into BM25 with Lucene non-negative IDFs."""
        self.chunks = list(chunks)
        self.corpus_tokens = []
        self.doc_lengths = []
        self.doc_freqs = Counter()

        for chunk in self.chunks:
            combined_search_text = (
                f"{chunk.law_name} مادة {chunk.article_number or ''} "
                f"{chunk.chapter or ''} {chunk.section or ''} {chunk.text_normalized}"
            )
            tokens = self.tokenize(combined_search_text)
            self.corpus_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            unique_terms = set(tokens)
            for t in unique_terms:
                self.doc_freqs[t] += 1

        n_docs = len(self.chunks)
        self.avgdl = sum(self.doc_lengths) / n_docs if n_docs > 0 else 0.0
        logger.info(f"BM25 index built with {n_docs} legal chunks (avgdl: {self.avgdl:.1f}).")

    def add_chunks(self, new_chunks: List[LegalChunk]) -> None:
        """Add new chunks, avoiding duplicate chunk IDs."""
        updated_ids = {c.chunk_id for c in new_chunks}
        surviving_chunks = [c for c in self.chunks if c.chunk_id not in updated_ids]
        surviving_chunks.extend(new_chunks)
        self.index_chunks(surviving_chunks)

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks associated with a document_id."""
        surviving = [c for c in self.chunks if c.document_id != document_id]
        if len(surviving) != len(self.chunks):
            self.index_chunks(surviving)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """
        Query BM25 index with Arabic legal query and optional metadata filters.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self.chunks)
        scored_pairs = []

        # Lucene BM25 scoring
        for idx, (doc_tokens, chunk) in enumerate(zip(self.corpus_tokens, self.chunks)):
            # Apply metadata filters if provided
            if filters and not self._matches_filter(chunk, filters):
                continue

            doc_len = self.doc_lengths[idx]
            term_counts = Counter(doc_tokens)
            score = 0.0

            for q_term in query_tokens:
                if q_term in term_counts:
                    f = term_counts[q_term]
                    df = self.doc_freqs.get(q_term, 0)
                    # Lucene non-negative IDF: ln(1 + (N - df + 0.5)/(df + 0.5))
                    idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                    # Term frequency normalization
                    numerator = f * (self.k1 + 1.0)
                    denominator = f + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl if self.avgdl > 0 else 1.0))
                    score += idf * (numerator / denominator)

            if score > 0.0:
                scored_pairs.append((score, chunk))

        # Sort descending by BM25 score
        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        top_pairs = scored_pairs[:top_k]

        results: List[RetrievedChunk] = []
        for score, chunk in top_pairs:
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    law_name=chunk.law_name,
                    law_number=chunk.law_number,
                    law_year=chunk.law_year,
                    article_number=chunk.article_number,
                    source_url=chunk.source_url,
                    chapter=chunk.chapter,
                    section=chunk.section,
                    score=float(score),
                    retrieval_method="sparse_bm25",
                    legal_status=chunk.legal_status
                )
            )

        return results

    @staticmethod
    def _matches_filter(chunk: LegalChunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk satisfies the provided metadata criteria."""
        for k, v in filters.items():
            if v is None or v == "":
                continue
            v_str = str(v).strip()
            chunk_val = getattr(chunk, k, None)
            if chunk_val is None:
                return False
            if k == "law_name":
                # Substring match for law name
                if v_str not in str(chunk_val):
                    return False
            elif str(chunk_val) != v_str:
                return False
        return True

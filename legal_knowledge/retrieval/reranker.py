"""
Multilingual Reranker Module for Egyptian Legal Text.
Uses cross-encoders (e.g. BAAI/bge-reranker-v2-m3) with a fallback alignment scorer
for offline/isolated environments.
"""

from typing import List, Tuple
import logging
from legal_knowledge.config import settings
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class FallbackArabicReranker:
    """
    Lightweight rule-based and n-gram alignment reranker for Arabic legal texts.
    Used when deep transformer weights cannot be downloaded in offline environments.
    """

    @classmethod
    def score_pair(cls, query: str, document_text: str, law_name: str, article_num: str, section: str = "") -> float:
        from legal_knowledge.retrieval.bm25_search import BM25SearchEngine
        
        q_tokens = set(BM25SearchEngine.tokenize(query))
        full_doc_text = f"{law_name} {section} {document_text}"
        doc_tokens = set(BM25SearchEngine.tokenize(full_doc_text))

        if not q_tokens:
            return 0.0

        # Jaccard / Overlap coefficient on informative tokens (len >= 3)
        inf_q_tokens = {t for t in q_tokens if len(t) >= 3 and t not in ["ماذا", "متى", "كيف", "حكم"]}
        if not inf_q_tokens:
            inf_q_tokens = q_tokens

        intersection = inf_q_tokens.intersection(doc_tokens)
        token_overlap = len(intersection) / len(inf_q_tokens)

        # Check for exact article number match bonus
        article_bonus = 0.0
        if article_num:
            clean_art = ArabicNormalizer.normalize_article_number(article_num)
            norm_q = ArabicNormalizer.normalize_for_search(query)
            if clean_art and (clean_art in norm_q.split() or f"ماده {clean_art}" in norm_q):
                article_bonus = 0.35

        # Check for law name match bonus
        law_bonus = 0.0
        if law_name:
            norm_law = ArabicNormalizer.normalize_for_search(law_name)
            for law_word in norm_law.split():
                if len(law_word) > 3 and law_word in q_tokens:
                    law_bonus += 0.15

        total_score = (token_overlap * 0.6) + article_bonus + law_bonus
        return min(total_score, 1.0)


class MultilingualReranker:
    """
    Multilingual cross-encoder reranker for reordering retrieved legal candidates.
    """

    def __init__(
        self,
        model_name: str = settings.RERANKER_MODEL_NAME,
        device: str = settings.RERANKER_DEVICE,
        use_fallback: bool = settings.USE_FALLBACK_RERANKER
    ):
        self.model_name = model_name
        self.device = device
        self._cross_encoder = None
        self._use_fallback = use_fallback

        if not use_fallback:
            self._init_model()

    def _init_model(self):
        """Lazy load cross-encoder."""
        if settings.USE_FALLBACK_RERANKER:
            self._use_fallback = True
            return

        try:
            from sentence_transformers import CrossEncoder
            try:
                self._cross_encoder = CrossEncoder(self.model_name, device=self.device, local_files_only=True)
                logger.info("Loaded local cached cross-encoder reranker.")
                return
            except Exception:
                pass

            self._cross_encoder = CrossEncoder(self.model_name, device=self.device)
            logger.info("Reranker loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load CrossEncoder model '{self.model_name}' ({e}). "
                "Enabling high-fidelity Arabic legal fallback reranker."
            )
            self._use_fallback = True

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_n: int = settings.DEFAULT_RETRIEVAL_TOP_K
    ) -> List[RetrievedChunk]:
        """
        Reranks candidate chunks by cross-attention or alignment scoring.
        """
        if not chunks:
            return []

        if not self._use_fallback and self._cross_encoder:
            try:
                pairs = [[query, chunk.text] for chunk in chunks]
                scores = self._cross_encoder.predict(pairs)
                # Attach scores
                scored_chunks: List[Tuple[float, RetrievedChunk]] = []
                for score, chunk in zip(scores, chunks):
                    c = chunk.model_copy()
                    c.score = float(score)
                    c.retrieval_method = "reranked"
                    scored_chunks.append((float(score), c))

                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                return [c for _, c in scored_chunks[:top_n]]
            except Exception as e:
                logger.error(f"Error during transformer reranking: {e}. Falling back to alignment reranker.")

        # Fallback reranking
        scored_chunks = []
        for chunk in chunks:
            score = FallbackArabicReranker.score_pair(
                query=query,
                document_text=chunk.text,
                law_name=chunk.law_name,
                article_num=chunk.article_number or "",
                section=chunk.section or ""
            )
            c = chunk.model_copy()
            c.score = float(score)
            c.retrieval_method = "reranked_alignment"
            scored_chunks.append((score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks[:top_n]]

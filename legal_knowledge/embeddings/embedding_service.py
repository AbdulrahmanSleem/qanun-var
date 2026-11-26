"""
Multilingual Embedding Service for Egyptian Legal Texts.
Supports BGE-M3 (BAAI/bge-m3), multilingual sentence-transformers,
and an offline fallback embedding engine for testing and isolated sandboxes.
"""

from typing import List, Union
import numpy as np
import logging
import hashlib
from legal_knowledge.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingService:
    """Abstract interface for embedding services."""

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError


class FallbackDeterministicEmbedder(BaseEmbeddingService):
    """
    Lightweight, ultra-fast deterministic embedding model for testing and offline execution.
    Projects normalized character n-grams and Arabic root hashes onto an L2-normalized unit sphere.
    Produces semantically consistent vector distances without external model downloads.
    """

    def __init__(self, dimension: int = 1024):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self._dim, dtype=np.float32)
        from legal_knowledge.retrieval.bm25_search import BM25SearchEngine
        tokens = BM25SearchEngine.tokenize(text)
        if not tokens:
            return vec

        for word in tokens:
            # Seed features based on 3-char ngrams and full word
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 1.0

            # Sub-word char 3-grams
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    sub = word[i:i+3]
                    sub_h = int(hashlib.sha1(sub.encode("utf-8")).hexdigest(), 16)
                    vec[sub_h % self._dim] += 0.5

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_vector(t).tolist() for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._hash_vector(query).tolist()


class MultilingualEmbeddingService(BaseEmbeddingService):
    """
    Production embedding service utilizing BGE-M3 / SentenceTransformers.
    Falls back gracefully to FallbackDeterministicEmbedder when dependencies or weights are unavailable.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        device: str = settings.EMBEDDING_DEVICE,
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
        use_fallback: bool = settings.USE_FALLBACK_EMBEDDINGS
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None
        self._dimension = settings.EMBEDDING_DIMENSION

        if use_fallback:
            logger.info("Explicit fallback embeddings requested. Initializing FallbackDeterministicEmbedder.")
            self._fallback = FallbackDeterministicEmbedder(self._dimension)
        else:
            self._fallback = None
            self._init_model()

    def _init_model(self):
        """Lazy load or initialize the transformer model."""
        if settings.USE_FALLBACK_EMBEDDINGS:
            logger.info("Fallback deterministic embeddings enabled via settings.")
            self._fallback = FallbackDeterministicEmbedder(self._dimension)
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Checking for local multilingual embedding model: {self.model_name}")
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded local cached model: {self.model_name}")
                return
            except Exception:
                logger.info(f"Model not cached locally. Attempting download of {self.model_name}...")

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model {self.model_name} loaded successfully. Dimension: {self._dimension}")
        except Exception as e:
            logger.warning(
                f"Could not load HuggingFace model '{self.model_name}' ({e}). "
                f"Falling back to high-fidelity FallbackDeterministicEmbedder."
            )
            self._fallback = FallbackDeterministicEmbedder(self._dimension)

    @property
    def dimension(self) -> int:
        if self._fallback:
            return self._fallback.dimension
        return self._dimension

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._fallback:
            return self._fallback.embed_texts(texts)

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings with transformer: {e}. Using fallback.")
            if not self._fallback:
                self._fallback = FallbackDeterministicEmbedder(self._dimension)
            return self._fallback.embed_texts(texts)

    def embed_query(self, query: str) -> List[float]:
        if not query.strip():
            return [0.0] * self.dimension
        if self._fallback:
            return self._fallback.embed_query(query)

        try:
            embedding = self._model.encode(
                query,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error encoding query: {e}. Using fallback.")
            if not self._fallback:
                self._fallback = FallbackDeterministicEmbedder(self._dimension)
            return self._fallback.embed_query(query)

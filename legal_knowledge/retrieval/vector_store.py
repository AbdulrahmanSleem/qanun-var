"""
Vector Store Implementation using Qdrant.

Supports embedded in-memory mode, local filesystem persistence, and remote Qdrant clusters.
Provides payload filtering (law_name, law_number, law_year, article_number, legal_status)
and deduplication/update guarantees.
"""

from typing import List, Optional, Dict, Any
import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from legal_knowledge.config import settings
from legal_knowledge.schemas.documents import LegalChunk
from legal_knowledge.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Production-grade Vector Store wrapping QdrantClient.
    
    Why Qdrant over PostgreSQL+pgvector:
    1. Zero-dependency embedded execution: Runs in-memory (:memory:) or local disk path
       for swift CI/CD and self-contained deployment, with 100% parity with remote clusters.
    2. Deep payload filtering: Native support for combining HNSW vector graphs with arbitrary
       metadata filters (law_number, law_year, article_number, legal_status).
    3. Production scalability: Effortlessly scales horizontally in Kubernetes/Docker clusters
       without adding relational schema migration complexity to team members.
    """

    def __init__(
        self,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
        vector_dim: int = settings.EMBEDDING_DIMENSION,
        client: Optional[QdrantClient] = None
    ):
        self.collection_name = collection_name
        self.vector_dim = vector_dim

        if client:
            self.client = client
        else:
            if settings.QDRANT_URL:
                logger.info(f"Connecting to remote Qdrant instance at {settings.QDRANT_URL}")
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
            else:
                location = settings.QDRANT_LOCATION or ":memory:"
                logger.info(f"Initializing local/embedded Qdrant instance: {location}")
                self.client = QdrantClient(location=location)

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """Create collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name} (dim: {self.vector_dim})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
                # Create payload indexes for frequent legal filter fields
                for field_name in ["law_name", "law_number", "law_year", "article_number", "document_id"]:
                    try:
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name=field_name,
                            field_schema=qmodels.PayloadSchemaType.KEYWORD
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {e}")

    @staticmethod
    def _to_uuid(chunk_id: str) -> str:
        """Generate deterministic UUID5 from string chunk_id for Qdrant point IDs."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def upsert_chunks(self, chunks: List[LegalChunk], embeddings: List[List[float]]) -> None:
        """
        Upsert legal chunks with their embeddings into Qdrant.
        Deterministic UUIDs ensure no duplicate chunks are created upon updates.
        """
        if not chunks:
            return

        points = []
        for chunk, emb in zip(chunks, embeddings):
            point_id = self._to_uuid(chunk.chunk_id)
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "text": chunk.text,  # authentic original text preserved
                "text_normalized": chunk.text_normalized,
                "law_name": chunk.law_name,
                "law_number": chunk.law_number,
                "law_year": chunk.law_year,
                "article_number": chunk.article_number,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "source_url": chunk.source_url,
                "publication_date": chunk.publication_date,
                "amendment_date": chunk.amendment_date,
                "legal_status": chunk.legal_status,
                "chunk_index": chunk.chunk_index,
            }
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        logger.info(f"Upserted {len(points)} chunks into Qdrant collection '{self.collection_name}'.")

    def delete_document(self, document_id: str) -> None:
        """Delete all indexed chunks belonging to a document_id."""
        logger.info(f"Deleting all chunks for document_id: {document_id}")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
            wait=True
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """
        Perform vector cosine similarity search with optional metadata filters.
        """
        qdrant_filter = self._build_qdrant_filter(filters)

        # qdrant-client search / query_points
        try:
            # query_points is the modern method in qdrant_client >= 1.7+
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True
            )
            points = response.points
        except Exception:
            # Fallback to search method
            points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True
            )

        retrieved: List[RetrievedChunk] = []
        for hit in points:
            payload = hit.payload or {}
            retrieved.append(
                RetrievedChunk(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    document_id=payload.get("document_id"),
                    text=payload.get("text", ""),
                    law_name=payload.get("law_name", ""),
                    law_number=payload.get("law_number"),
                    law_year=payload.get("law_year"),
                    article_number=payload.get("article_number"),
                    source_url=payload.get("source_url"),
                    chapter=payload.get("chapter"),
                    section=payload.get("section"),
                    score=float(hit.score),
                    retrieval_method="dense",
                    legal_status=payload.get("legal_status")
                )
            )

        return retrieved

    def _build_qdrant_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[qmodels.Filter]:
        """Convert dictionary filters to Qdrant Filter conditions."""
        if not filters:
            return None

        must_conditions = []
        for key, value in filters.items():
            if value is not None and value != "":
                must_conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=str(value))
                    )
                )

        if not must_conditions:
            return None

        return qmodels.Filter(must=must_conditions)

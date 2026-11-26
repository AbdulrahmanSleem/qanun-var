"""
Retrieval request and response schemas for QANUN-VAR.
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class RetrievedChunk(BaseModel):
    """
    Standard retrieved legal chunk structure consumed by F1 (Legal Q&A),
    F2 (Contract Review), and F3 (Case Analysis).
    """

    model_config = ConfigDict(extra="ignore")

    chunk_id: str = Field(..., description="Unique chunk ID")
    document_id: Optional[str] = Field(default=None, description="Parent document identifier")
    text: str = Field(..., description="Original authentic legal text")
    law_name: str = Field(..., description="Name of the law")
    law_number: Optional[str] = Field(default=None, description="Law number")
    law_year: Optional[str] = Field(default=None, description="Law year")
    article_number: Optional[str] = Field(default=None, description="Article number")
    source_url: Optional[str] = Field(default=None, description="Official source reference")
    
    # Enrichment fields for transparency and reranking
    chapter: Optional[str] = Field(default=None, description="Chapter/Door hierarchy")
    section: Optional[str] = Field(default=None, description="Section hierarchy")
    score: float = Field(default=0.0, description="Relevance score from hybrid search / reranker")
    retrieval_method: Optional[str] = Field(
        default="hybrid",
        description="Retrieval origin: 'dense', 'sparse_bm25', 'hybrid', 'reranked'"
    )
    legal_status: Optional[str] = Field(default=None, description="Verified legal status if available")


class RetrievalFilter(BaseModel):
    """Metadata filters for targeted retrieval."""

    model_config = ConfigDict(extra="ignore")

    law_name: Optional[str] = Field(default=None, description="Filter by law name (substring or exact)")
    law_number: Optional[str] = Field(default=None, description="Filter by official law number")
    law_year: Optional[str] = Field(default=None, description="Filter by year of issuance")
    article_number: Optional[str] = Field(default=None, description="Filter by specific article number")
    legal_status: Optional[str] = Field(default=None, description="Filter by verified status (e.g. 'in_force')")
    document_type: Optional[str] = Field(default=None, description="Filter by document type")


class RetrievalRequest(BaseModel):
    """API request model for legal source retrieval."""

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="Legal query in Arabic or English")
    filters: Optional[dict[str, Any]] = Field(default=None, description="Metadata filters")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    method: Literal["dense", "sparse", "hybrid"] = Field(
        default="hybrid",
        description="Retrieval engine to use"
    )
    apply_reranking: bool = Field(default=True, description="Whether to apply cross-encoder reranking")


class RetrievalResponse(BaseModel):
    """API response model containing retrieved legal chunks."""

    model_config = ConfigDict(extra="ignore")

    query: str
    total_found: int
    results: list[RetrievedChunk]
    latency_ms: float
    retrieval_method_used: str
    reranked: bool

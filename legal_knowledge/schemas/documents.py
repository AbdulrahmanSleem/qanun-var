"""
Document and Chunk Schemas for Egyptian Legal Knowledge Base.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class LegalDocument(BaseModel):
    """Represents an ingested legal document (e.g., an entire statutory code or act)."""

    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(..., description="Unique deterministic identifier for the document")
    title: str = Field(..., description="Title or official heading of the legal document")
    law_name: str = Field(..., description="Official name of the law, e.g., 'القانون المدني المصري'")
    law_number: Optional[str] = Field(default=None, description="Official law number, e.g., '131'")
    law_year: Optional[str] = Field(default=None, description="Promulgation year, e.g., '1948'")
    document_type: str = Field(default="law", description="Type: 'law', 'decree', 'court_ruling', etc.")
    source_url: Optional[str] = Field(default=None, description="Official source URL or reference link")
    publication_date: Optional[str] = Field(default=None, description="Official gazette publication date")
    amendment_date: Optional[str] = Field(default=None, description="Date of latest recorded amendment")
    legal_status: Optional[str] = Field(
        default=None,
        description="Legal status: 'in_force', 'amended', 'repealed' (only when verified)"
    )
    raw_text: Optional[str] = Field(default=None, description="Full extracted raw text before chunking")
    file_path: Optional[str] = Field(default=None, description="Original source file path")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LegalChunk(BaseModel):
    """
    Represents an atomic legal chunk (typically an individual legal article 'مادة').
    Maintains dual text representations: original (for quotation/display) and normalized (for search).
    """

    model_config = ConfigDict(extra="ignore")

    chunk_id: str = Field(..., description="Unique deterministic identifier for the chunk")
    document_id: str = Field(..., description="Parent document identifier")
    
    # Dual text representations
    text: str = Field(..., description="ORIGINAL legal text preserved verbatim for citations and quotations")
    text_normalized: str = Field(..., description="NORMALIZED text used exclusively for lexical and semantic indexing")
    
    # Legal metadata
    law_name: str = Field(..., description="Name of the law, e.g., 'قانون العمل رقم 12 لسنة 2003'")
    law_number: Optional[str] = Field(default=None, description="Official law number")
    law_year: Optional[str] = Field(default=None, description="Year of issuance")
    article_number: Optional[str] = Field(default=None, description="Article number, e.g., '123' or '4 مكرر'")
    chapter: Optional[str] = Field(default=None, description="Chapter/Part hierarchy, e.g., 'الباب الأول'")
    section: Optional[str] = Field(default=None, description="Section hierarchy, e.g., 'الفصل الثاني'")
    source_url: Optional[str] = Field(default=None, description="Official source URL")
    publication_date: Optional[str] = Field(default=None, description="Official publication date")
    amendment_date: Optional[str] = Field(default=None, description="Latest amendment date if verified")
    legal_status: Optional[str] = Field(default=None, description="Verified legal status, null if unverified")
    
    # Structural details
    chunk_index: int = Field(default=0, description="Sequential index within document")
    token_count: int = Field(default=0, description="Approximate token count")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

"""
Citation verification schemas for QANUN-VAR.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class Citation(BaseModel):
    """Represents a citation made in an AI-generated legal answer or review."""

    model_config = ConfigDict(extra="ignore")

    law_name: str = Field(..., description="Cited law name")
    law_number: Optional[str] = Field(default=None, description="Cited law number")
    law_year: Optional[str] = Field(default=None, description="Cited law year")
    article_number: Optional[str] = Field(default=None, description="Cited article number")
    quoted_text: Optional[str] = Field(default=None, description="Quoted legal text")
    claim_text: Optional[str] = Field(default=None, description="The legal claim being supported")
    is_verified: bool = Field(default=False, description="Whether citation passed all verification checks")
    verification_status: Literal["verified", "invalid", "unsupported", "partial", "unverified"] = Field(
        default="unverified"
    )
    verification_details: Optional[str] = Field(default=None, description="Detailed explanation of verification")


class CitationVerificationResult(BaseModel):
    """Full report produced by CitationVerifier."""

    model_config = ConfigDict(extra="ignore")

    is_valid: bool = Field(..., description="Overall validity of the citation")
    law_matched: bool = Field(..., description="True if law exists in the retrieved knowledge base")
    article_matched: bool = Field(..., description="True if article number exists in the retrieved chunks")
    quote_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Lexical/semantic similarity between quote and official source text"
    )
    quote_verified: bool = Field(..., description="True if quoted text matches official text within threshold")
    claim_supported: bool = Field(..., description="True if retrieved article logically supports the claim")
    matched_chunk_id: Optional[str] = Field(default=None, description="ID of chunk that verified this citation")
    official_legal_text: Optional[str] = Field(
        default=None,
        description="The authentic original legal text from the verified source"
    )
    warnings: list[str] = Field(default_factory=list, description="Warning messages or discrepancies detected")
    reasoning: str = Field(..., description="Summary explanation of the verification outcome")

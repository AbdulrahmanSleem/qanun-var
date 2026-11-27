"""
Pydantic schemas for the QANUN-VAR Legal Knowledge & Retrieval System.
"""

from legal_knowledge.schemas.documents import LegalDocument, LegalChunk
from legal_knowledge.schemas.retrieval import (
    RetrievedChunk,
    RetrievalFilter,
    RetrievalRequest,
    RetrievalResponse,
)
from legal_knowledge.schemas.citations import Citation, CitationVerificationResult
from legal_knowledge.schemas.agent import AgentRequest, AgentContext, AgentResult

__all__ = [
    "LegalDocument",
    "LegalChunk",
    "RetrievedChunk",
    "RetrievalFilter",
    "RetrievalRequest",
    "RetrievalResponse",
    "Citation",
    "CitationVerificationResult",
    "AgentRequest",
    "AgentContext",
    "AgentResult",
]

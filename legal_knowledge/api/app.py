"""
FastAPI Service Interfaces for QANUN-VAR Legal Knowledge & Retrieval System.
Provides REST API endpoints consumable by Member 1 (Frontend), Member 3 (Contract Review),
Member 4 (Case Analysis), and the Backend Orchestrator.
"""

from typing import List, Optional, Dict, Any
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from legal_knowledge.config import settings
from legal_knowledge.schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievedChunk
from legal_knowledge.schemas.agent import AgentRequest, AgentContext, AgentResult
from legal_knowledge.schemas.citations import Citation, CitationVerificationResult
from legal_knowledge.retrieval.retrieval_service import get_retrieval_service
from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
from legal_knowledge.citations.citation_verifier import CitationVerifier
from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline


app = FastAPI(
    title="QANUN-VAR: Egyptian Legal Knowledge & Retrieval Service",
    description="Production-grade Egyptian Legal Knowledge Base, Hybrid Retrieval, Legal Q&A Agent, and Citation Verifier.",
    version=settings.VERSION,
)

# CORS configuration for integration with frontend and backend services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared service instances
retrieval_service = get_retrieval_service()
qa_agent = LegalQAAgent(retrieval_service=retrieval_service)
citation_verifier = CitationVerifier()
ingestion_pipeline = LegalIngestionPipeline(retrieval_service=retrieval_service)


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Raw text of the legal statute")
    law_name: Optional[str] = Field(default=None, description="Official law title")
    law_number: Optional[str] = Field(default=None, description="Official law number")
    law_year: Optional[str] = Field(default=None, description="Promulgation year")
    source_url: Optional[str] = Field(default=None, description="Official source reference")
    legal_status: Optional[str] = Field(default=None, description="Verified legal status ('in_force', etc.)")


class IngestResponse(BaseModel):
    document_id: str
    law_name: str
    total_articles: int
    message: str


class VerifyCitationRequest(BaseModel):
    citation: Citation
    retrieved_chunks: List[RetrievedChunk]


@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """Healthcheck endpoint detailing service configuration and status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "vector_store": settings.VECTOR_STORE_BACKEND,
        "reranker": settings.RERANKER_MODEL_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.post("/api/v1/retrieve", response_model=RetrievalResponse, tags=["Retrieval"])
async def retrieve_legal_sources(request: RetrievalRequest):
    """
    Shared Legal Retrieval Service endpoint.
    Consumable by F1 (Legal Q&A), F2 (Contract Review), and F3 (Case Analysis).
    """
    start_time = time.perf_counter()
    try:
        results = await retrieval_service.search_legal_sources(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k,
            method=request.method,
            apply_reranking=request.apply_reranking
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResponse(
            query=request.query,
            total_found=len(results),
            results=results,
            latency_ms=elapsed_ms,
            retrieval_method_used=request.method,
            reranked=request.apply_reranking
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(e)}"
        )


@app.post("/api/v1/qa", response_model=AgentResult, tags=["Legal Q&A Agent"])
async def answer_legal_question(request: AgentRequest):
    """
    Execute the Legal Q&A Agent.
    Retrieves authentic Egyptian legal articles, synthesizes plain-language explanations,
    verifies citations, and distinguishes verbatim legal text from AI interpretation.
    """
    try:
        context = AgentContext()
        result = await qa_agent.run(request, context)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Legal Q&A Agent execution error: {str(e)}"
        )


@app.post("/api/v1/verify-citation", response_model=CitationVerificationResult, tags=["Citations"])
async def verify_single_citation(request: VerifyCitationRequest):
    """
    Verify citation validity against retrieved legal articles.
    Checks law existence, article number, quote accuracy, and claim support.
    """
    try:
        report = citation_verifier.verify_citation(
            citation=request.citation,
            retrieved_chunks=request.retrieved_chunks
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation verification error: {str(e)}"
        )


@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_legal_text(request: IngestTextRequest):
    """
    Ingest a legal document through the complete 9-stage pipeline.
    """
    try:
        provided_meta = {
            "law_name": request.law_name,
            "law_number": request.law_number,
            "law_year": request.law_year,
            "legal_status": request.legal_status,
        }
        doc, chunks = ingestion_pipeline.ingest_raw_text(
            text=request.text,
            source_url=request.source_url,
            provided_metadata=provided_meta
        )
        return IngestResponse(
            document_id=doc.document_id,
            law_name=doc.law_name,
            total_articles=len(chunks),
            message="Document successfully processed and indexed into knowledge base."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document ingestion error: {str(e)}"
        )

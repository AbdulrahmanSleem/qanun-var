
"""Thin FastAPI layer: exposes the Orchestrator as endpoints for Streamlit.
Also owns document conversion/OCR confirmation endpoints."""
from fastapi import FastAPI, UploadFile
from shared.schemas import AgentRequest, AgentResponse, Intent
from shared import document_service
import graph

app = FastAPI(title="QANUN-VAR API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agent/run", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    return graph.run(request)


@app.post("/documents/upload")
def upload(file: UploadFile):
    """Store raw file, run extraction, return extracted text + whether
    human confirmation is required (OCR guardrail)."""
    raise NotImplementedError  # TODO [ElMelegy/Mo3taz]


@app.post("/documents/{doc_id}/confirm")
def confirm(doc_id: str, corrected_text: str):
    document_service.confirm_text(doc_id, corrected_text)
    return {"status": "confirmed"}

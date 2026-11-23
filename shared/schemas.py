
"""QANUN-VAR unified schemas — SINGLE SOURCE OF TRUTH.
Every agent consumes and returns these pydantic models. Do not add
feature-specific fields to shared models; extend in your own agent module.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    LEGAL_QA = "legal_qa"
    CONTRACT_REVIEW = "contract_review"
    CASE_ANALYSIS = "case_analysis"
    CONTRACT_GENERATION = "contract_generation"


class Citation(BaseModel):
    """One verified legal source backing (part of) an answer."""
    law_name: str
    law_number: str
    article_number: str
    article_text: str
    chapter: Optional[str] = None
    last_amendment: Optional[str] = None


class AgentRequest(BaseModel):
    """What the Orchestrator hands to every agent."""
    intent: Intent
    text: Optional[str] = None                 # question / case text
    file_id: Optional[str] = None              # uploaded document (OCR confirmed)
    party_role: Optional[str] = None           # F2: first/second party
    contract_type: Optional[str] = None        # F2/F4
    questionnaire: Optional[dict] = None       # F4: guided answers
    session_id: str = "default"


class VerifiedAnswer(BaseModel):
    """Result that passed (or failed) the Citation Verifier."""
    answer_text: str
    citations: list[Citation] = Field(default_factory=list)
    verifier_passed: bool = False
    verifier_notes: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """What every agent must return via run_agent()."""
    agent_name: str
    status: str = "ok"                         # ok | refused | degraded | error
    result: Optional[VerifiedAnswer] = None
    artifacts: dict = Field(default_factory=dict)   # e.g. {"docx_path": ...}
    error: Optional[str] = None

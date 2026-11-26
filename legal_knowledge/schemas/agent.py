"""
Agent interface schemas for QANUN-VAR Legal Q&A Agent.
These conform to the shared contract for Member 2 integration.
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.schemas.citations import Citation, CitationVerificationResult


class AgentRequest(BaseModel):
    """
    Standard request envelope passed to the Legal Q&A Agent.
    Conforms to the shared team interface contract.
    """

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="The user's legal question in Arabic or English")
    user_id: Optional[str] = Field(default="anonymous_user", description="Identifier for the user")
    session_id: Optional[str] = Field(default=None, description="Active conversation or case session ID")
    filters: Optional[dict[str, Any]] = Field(default=None, description="Optional metadata filters for retrieval")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context or flags")


class AgentContext(BaseModel):
    """
    Runtime execution context supplied by the Backend Orchestrator.
    """

    model_config = ConfigDict(extra="ignore")

    session_state: dict[str, Any] = Field(default_factory=dict, description="Session state from orchestrator")
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Prior conversation turns [{'role': 'user'|'assistant', 'content': '...'}]"
    )
    user_role: Optional[str] = Field(default="client", description="User role: 'client', 'lawyer', 'judge'")
    system_instructions: Optional[str] = Field(
        default=None,
        description="Optional custom override instructions from orchestrator"
    )


class LegalIntent(BaseModel):
    """Structured legal intent extracted from user query."""

    model_config = ConfigDict(extra="ignore")

    intent_type: Literal[
        "article_inquiry",
        "legal_rule_inquiry",
        "penalty_inquiry",
        "rights_and_obligations",
        "procedural_inquiry",
        "general_inquiry"
    ] = Field(default="general_inquiry")
    target_law: Optional[str] = Field(default=None, description="Targeted law if mentioned in question")
    target_article: Optional[str] = Field(default=None, description="Targeted article number if mentioned")
    keywords: list[str] = Field(default_factory=list, description="Extracted Arabic legal keywords")


class AgentResult(BaseModel):
    """
    Structured outcome returned by the Legal Q&A Agent to the Orchestrator.
    Ensures clear distinction between authentic legal text and AI explanation.
    """

    model_config = ConfigDict(extra="ignore")

    status: Literal["answered", "abstained", "clarification_needed"] = Field(
        ...,
        description="Outcome status: answered, abstained (insufficient sources), clarification_needed"
    )
    answer: str = Field(..., description="Comprehensive answer synthesized for the user")
    legal_explanation: str = Field(
        ...,
        description="AI plain-language explanation of the legal rule in clear Arabic"
    )
    official_legal_quotations: list[str] = Field(
        default_factory=list,
        description="Verbatim text of relevant articles directly from verified sources"
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of verified citations with law and article references"
    )
    verification_reports: list[CitationVerificationResult] = Field(
        default_factory=list,
        description="Detailed verification results for each citation"
    )
    supporting_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Retrieved supporting legal articles used in reasoning"
    )
    abstention_reason: Optional[str] = Field(
        default=None,
        description="Reason for abstaining if reliable supporting sources are unavailable"
    )
    disclaimer: str = Field(
        default=(
            "تنبيه قانوني: هذه المعلومات مقدمة لأغراض استرشادية وبحثية وفق التشريعات المصرية المتاحة، "
            "ولا تعد استشارة قانونية رسمية أو بديلاً عن توكيل محامٍ مقيد."
        ),
        description="Mandatory legal disclaimer"
    )
    latency_ms: float = Field(default=0.0, description="End-to-end execution latency in milliseconds")

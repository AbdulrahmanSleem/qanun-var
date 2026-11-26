"""Feature 1: Legal Q&A — full implementation.

Owner: Ali
Delegates to legal_knowledge.agents.legal_qa_agent.LegalQAAgent which runs:
  question → retrieve → rerank → prompt → LLM → citation_verify → VerifiedAnswer
"""
from __future__ import annotations

import asyncio
import logging
import sys
import os
from typing import Optional

logger = logging.getLogger(__name__)

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from shared.schemas import (
    AgentRequest,
    AgentResponse,
    Citation,
    VerifiedAnswer,
)


def run_agent(request: AgentRequest) -> AgentResponse:
    """Entry-point called by the Orchestrator for Feature 1.

    Args:
        request: Shared AgentRequest (intent=LEGAL_QA, text=Arabic/English question).

    Returns:
        AgentResponse with VerifiedAnswer and all citations validated against
        the indexed knowledge base.
    """
    try:
        from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
        from legal_knowledge.schemas.agent import (
            AgentRequest as _LocalRequest,
            AgentContext,
        )

        agent = LegalQAAgent()
        local_req = _LocalRequest(
            query=request.text or "",
            session_id=request.session_id,
        )
        result = asyncio.run(agent.run(local_req, AgentContext()))

        # Map local Citation → shared Citation
        citations: list[Citation] = []
        for c in result.citations:
            if c.is_verified:
                citations.append(
                    Citation(
                        law_name=c.law_name or "",
                        law_number=c.law_number or "",
                        article_number=c.article_number or "",
                        article_text=c.quoted_text or "",
                        chapter=getattr(c, "chapter", None),
                        last_amendment=None,
                    )
                )

        verifier_notes: list[str] = [
            r.reasoning
            for r in getattr(result, "verification_reports", [])
            if getattr(r, "reasoning", None)
        ]

        status = "ok" if result.status == "answered" else "refused"

        return AgentResponse(
            agent_name="legal_qa",
            status=status,
            result=VerifiedAnswer(
                answer_text=result.answer,
                citations=citations,
                verifier_passed=bool(citations),
                verifier_notes=verifier_notes or (
                    ["لم يتم التحقق من أي مصادر"] if not citations else []
                ),
            ),
        )

    except Exception as exc:  # pragma: no cover
        logger.error("run_agent (legal_qa) failed: %s", exc, exc_info=True)
        return AgentResponse(
            agent_name="legal_qa",
            status="error",
            error=str(exc),
        )

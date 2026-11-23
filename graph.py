
"""LangGraph Orchestrator: intent classification -> route to agent -> Citation Verifier gate.
Day 2 gate: routes all four intents to mock agents end-to-end.
"""
from shared.schemas import AgentRequest, AgentResponse, Intent
from agents import (legal_qa_agent, contract_review_agent,
                    case_analysis_agent, contract_generation_agent)

_ROUTES = {
    Intent.LEGAL_QA: legal_qa_agent,
    Intent.CONTRACT_REVIEW: contract_review_agent,
    Intent.CASE_ANALYSIS: case_analysis_agent,
    Intent.CONTRACT_GENERATION: contract_generation_agent,
}


def classify_intent(request: AgentRequest) -> AgentRequest:
    """TODO [Sleem]: rule-based start ('عقد/مراجعة' -> review etc.),
    LLM classification fallback via shared.llm_service.generate."""
    return request


def verify_citations(response: AgentResponse) -> AgentResponse:
    """TODO [Ali]: deterministic check — every article_number in the answer
    exists in the retrieved passages. Fail -> status='refused', keep notes."""
    return response


def run(request: AgentRequest) -> AgentResponse:
    request = classify_intent(request)
    response = _ROUTES[request.intent](request)
    return verify_citations(response)


"""Feature 1: Legal Q&A — scaffold. MOCK first (Day 2 gate), real logic after."""
from shared.schemas import AgentRequest, AgentResponse, VerifiedAnswer, Citation


def run_agent(request: AgentRequest) -> AgentResponse:
    # Day 2: return a placeholder that satisfies the schema.
    return AgentResponse(
        agent_name="legal_qa",
        result=VerifiedAnswer(
            answer_text="إجابة مؤقتة (placeholder — real logic lands after Gate 1)",
            citations=[],
            verifier_passed=False,
            verifier_notes=["mock response, not verified"],
        ),
    )

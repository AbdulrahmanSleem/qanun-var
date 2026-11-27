"""
Tests for Legal Q&A Agent and Hallucination Prevention.
"""

import pytest
from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
from legal_knowledge.schemas.agent import AgentRequest, AgentContext


@pytest.mark.asyncio
async def test_legal_qa_answering(test_qa_agent: LegalQAAgent):
    request = AgentRequest(
        query="ما هي أقصى مدة لفترة الاختبار في عقد العمل الفردي في مصر؟"
    )
    context = AgentContext()

    result = await test_qa_agent.run(request, context)

    assert result.status == "answered"
    assert "31" in result.answer or "ثلاثة أشهر" in result.answer
    assert len(result.citations) > 0
    assert result.citations[0].is_verified is True
    assert len(result.official_legal_quotations) > 0
    assert result.disclaimer != ""


@pytest.mark.asyncio
async def test_legal_qa_abstention_out_of_scope(test_qa_agent: LegalQAAgent):
    # Query completely outside the ingested Civil and Labor code knowledge base
    request = AgentRequest(
        query="ما هي عقوبات المخالفات الجمركية والتهريب في قانون الجمارك؟"
    )

    result = await test_qa_agent.run(request)

    assert result.status == "abstained"
    assert "لا تتوفر في قاعدة المعرفة" in result.answer
    assert result.abstention_reason is not None
    # Must not fabricate citations
    assert len(result.citations) == 0 or all(not c.is_verified for c in result.citations)

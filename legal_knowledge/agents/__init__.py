"""
Agents module exports.
"""

from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
from legal_knowledge.agents.llm_service import (
    BaseLLMService,
    MockLegalLLMService,
    GeminiLLMService,
    OpenAILLMService,
    get_llm_service,
)
from legal_knowledge.agents.prompts import (
    LEGAL_QA_SYSTEM_PROMPT,
    LEGAL_QA_USER_TEMPLATE,
    format_retrieved_context,
)

__all__ = [
    "LegalQAAgent",
    "BaseLLMService",
    "MockLegalLLMService",
    "GeminiLLMService",
    "OpenAILLMService",
    "get_llm_service",
    "LEGAL_QA_SYSTEM_PROMPT",
    "LEGAL_QA_USER_TEMPLATE",
    "format_retrieved_context",
]

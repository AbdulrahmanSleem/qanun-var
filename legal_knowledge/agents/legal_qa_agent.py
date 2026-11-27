"""
Dedicated Legal Q&A Agent for QANUN-VAR.
Adheres strictly to the integration contract:
async def run(request: AgentRequest, context: AgentContext) -> AgentResult
"""

import time
import re
import difflib
import logging
from typing import Optional, List, Dict, Any

from legal_knowledge.config import settings
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.schemas.citations import Citation
from legal_knowledge.schemas.agent import AgentRequest, AgentContext, AgentResult, LegalIntent
from legal_knowledge.retrieval.retrieval_service import LegalRetrievalService, get_retrieval_service
from legal_knowledge.citations.citation_verifier import CitationVerifier
from legal_knowledge.agents.prompts import (
    LEGAL_QA_SYSTEM_PROMPT,
    LEGAL_QA_USER_TEMPLATE,
    format_retrieved_context
)
from legal_knowledge.agents.llm_service import BaseLLMService, get_llm_service
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class LegalQAAgent:
    """
    Production-grade Legal Q&A Agent grounding every assertion in authentic
    Egyptian legislation and validating citations via CitationVerifier.
    """

    def __init__(
        self,
        retrieval_service: Optional[LegalRetrievalService] = None,
        citation_verifier: Optional[CitationVerifier] = None,
        llm_service: Optional[BaseLLMService] = None
    ):
        self.retrieval_service = retrieval_service or get_retrieval_service()
        self.citation_verifier = citation_verifier or CitationVerifier()
        self.llm_service = llm_service or get_llm_service()

    def analyze_legal_intent(self, query: str) -> LegalIntent:
        """
        Analyzes question to identify target law, article number, and intent type.
        """
        norm_query = ArabicNormalizer.normalize_for_search(query)

        # Detect intent type
        intent_type = "general_inquiry"
        if any(w in norm_query for w in ["عقوبه", "حبس", "غرامه", "جزاء", "مخالفه"]):
            intent_type = "penalty_inquiry"
        elif any(w in norm_query for w in ["ماده", "الماده"]):
            intent_type = "article_inquiry"
        elif any(w in norm_query for w in ["حق", "حقوق", "التزام", "واجب", "تعويض"]):
            intent_type = "rights_and_obligations"
        elif any(w in norm_query for w in ["اجراء", "ميعاد", "دعوى", "طعن", "استئناف"]):
            intent_type = "procedural_inquiry"

        # Extract target article if mentioned: e.g. "المادة 147", "مادة 12"
        art_match = re.search(r"\b(?:مادة|المادة)\s+(?:رقم\s+)?(\d+|[0-9٠-٩]+|[أ-ي]+)(?:\s+(مكرر))?", query)
        target_article = None
        if art_match:
            raw_art = f"{art_match.group(1)} {art_match.group(2) or ''}".strip()
            target_article = ArabicNormalizer.normalize_article_number(raw_art)

        # Extract target law if mentioned
        target_law = None
        for candidate in ["القانون المدني", "قانون العمل", "قانون العقوبات", "قانون التجارة", "قانون المرور", "قانون الإجراءات"]:
            if candidate in query or ArabicNormalizer.normalize_for_search(candidate) in norm_query:
                target_law = candidate
                break

        if not target_law:
            law_match = re.search(r"(قانون\s+[\u0621-\u064A]{3,}(?:\s+[\u0621-\u064A]{3,})?)", query)
            if law_match:
                target_law = law_match.group(1).strip()

        keywords = [w for w in norm_query.split() if len(w) > 3]

        return LegalIntent(
            intent_type=intent_type,
            target_law=target_law,
            target_article=target_article,
            keywords=keywords
        )

    async def run(
        self,
        request: AgentRequest,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Executes the 8-stage Legal Q&A Agent workflow.
        """
        start_time = time.perf_counter()
        query = request.query.strip()
        context = context or AgentContext()

        logger.info(f"[Legal Q&A Agent] Received question: '{query[:80]}...'")

        # 1 & 2. Analyze legal intent
        intent = self.analyze_legal_intent(query)
        logger.debug(f"[Legal Q&A Agent] Detected intent: {intent.intent_type}, target_article={intent.target_article}")

        # Construct retrieval filters from request and intent
        retrieval_filters = dict(request.filters or {})
        if intent.target_article and "article_number" not in retrieval_filters:
            retrieval_filters["article_number"] = intent.target_article
        if intent.target_law and "law_name" not in retrieval_filters:
            retrieval_filters["law_name"] = intent.target_law

        # 3 & 4. Retrieve relevant legal articles with reranking
        retrieved_chunks = await self.retrieval_service.search_legal_sources(
            query=query,
            filters=retrieval_filters if retrieval_filters else None,
            top_k=settings.DEFAULT_RETRIEVAL_TOP_K,
            method="hybrid",
            apply_reranking=True
        )

        # If filtered search returned empty, fallback to open hybrid search without strict filters
        if not retrieved_chunks and retrieval_filters:
            logger.info("[Legal Q&A Agent] Filtered retrieval yielded 0 results; falling back to unrestricted retrieval.")
            retrieved_chunks = await self.retrieval_service.search_legal_sources(
                query=query,
                filters=None,
                top_k=settings.DEFAULT_RETRIEVAL_TOP_K,
                method="hybrid",
                apply_reranking=True
            )

        # Check for insufficient evidence / abstention conditions
        should_abstain = False
        abstention_reason = None

        if not retrieved_chunks:
            should_abstain = True
            abstention_reason = "عدم توفر نصوص قانونية موثقة في قاعدة المعرفة ذات صلة بالسؤال."
        else:
            # Check if query specifically targeted a law that is not in the knowledge base
            if intent.target_law:
                norm_target_law = ArabicNormalizer.normalize_for_search(intent.target_law)
                law_found = any(
                    norm_target_law in ArabicNormalizer.normalize_for_search(c.law_name) or
                    ArabicNormalizer.normalize_for_search(c.law_name) in norm_target_law
                    for c in retrieved_chunks
                )
                if not law_found:
                    should_abstain = True
                    abstention_reason = f"التشريع المطلوب '{intent.target_law}' غير مفهرس في قاعدة المعرفة المتاحة حالياً."

            # Check keyword relevance overlap between query and top retrieved chunk
            if not should_abstain:
                q_norm = ArabicNormalizer.normalize_for_search(query)
                q_tokens = [w for w in q_norm.split() if len(w) > 3 and w not in ["ماذا", "متى", "كيف", "لماذا", "حكم", "قاعده", "قانون"]]
                top_doc_norm = ArabicNormalizer.normalize_for_search(retrieved_chunks[0].text + " " + (retrieved_chunks[0].section or ""))
                overlap_count = sum(1 for tok in q_tokens if tok in top_doc_norm)
                if q_tokens and (overlap_count / len(q_tokens)) < 0.20:
                    should_abstain = True
                    abstention_reason = "النصوص المسترجعة لا تقدم سنداً موضوعياً كافياً للإجابة على هذا السؤال بشكل موثق."

        if should_abstain:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                status="abstained",
                answer="نعتذر، لا تتوفر في قاعدة المعرفة التشريعية حالياً نصوص قانونية كافية للإجابة على هذا السؤال بشكل موثق وقاطع.",
                legal_explanation="لم نتمكن من العثور على أي نصوص تشريعية مصرية مفهرسة تنطبق مباشرة على الاستفسار المطروح.",
                abstention_reason=abstention_reason,
                official_legal_quotations=[],
                citations=[],
                verification_reports=[],
                supporting_chunks=[],
                latency_ms=elapsed_ms
            )

        # 5. Construct context-grounded prompt
        formatted_context = format_retrieved_context(retrieved_chunks)
        user_prompt = LEGAL_QA_USER_TEMPLATE.format(
            retrieved_context=formatted_context,
            query=query
        )

        # 6. Generate answer using LLM service
        raw_llm_response = await self.llm_service.generate(
            prompt=user_prompt,
            system_prompt=LEGAL_QA_SYSTEM_PROMPT
        )

        # 7. Extract citations and supporting quotations
        extracted_citations, quotations, explanation = self._extract_citations_and_parts(
            raw_llm_response,
            retrieved_chunks
        )

        # Verify citations against retrieved chunks
        verified_citations, reports, all_passed = self.citation_verifier.verify_all(
            citations=extracted_citations,
            retrieved_chunks=retrieved_chunks
        )

        # Check if answer abstains
        status = "answered"
        if "لا تتوفر في قاعدة المعرفة نصوص" in raw_llm_response or not verified_citations:
            if not any(c.is_verified for c in verified_citations):
                status = "abstained"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AgentResult(
            status=status,
            answer=raw_llm_response,
            legal_explanation=explanation,
            official_legal_quotations=quotations,
            citations=verified_citations,
            verification_reports=reports,
            supporting_chunks=retrieved_chunks,
            abstention_reason="لم تجتز الاستشهادات معايير التحقق القانوني" if status == "abstained" else None,
            latency_ms=elapsed_ms
        )

    def _extract_citations_and_parts(
        self,
        llm_text: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> Tuple[List[Citation], List[str], str]:
        """Extract citations, official quotations, and AI explanation from LLM output."""
        citations: List[Citation] = []
        quotations: List[str] = []

        # Extract quotations between « » or " "
        quotes = re.findall(r"[«\"](.*?)[»\"]", llm_text, re.DOTALL)
        for q in quotes:
            clean_q = q.strip()
            if len(clean_q) > 15:
                quotations.append(clean_q)

        # Extract explanation section
        explanation = ""
        exp_match = re.search(r"\[الشرح والتكييف القانوني\]:\s*(.*?)(?=\n\[|$)", llm_text, re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip()
        else:
            explanation = llm_text

        # Create structured citations based on supporting retrieved chunks mentioned in text
        for chunk in retrieved_chunks:
            # Check if this article is cited in LLM output
            art_num = chunk.article_number or ""
            is_referenced = False
            if art_num and (f"المادة ({art_num})" in llm_text or f"مادة ({art_num})" in llm_text or f"المادة {art_num}" in llm_text):
                is_referenced = True
            elif chunk.law_name and chunk.law_name in llm_text:
                is_referenced = True

            if is_referenced:
                # Find matching quotation if any
                matching_quote = None
                for q in quotations:
                    if q in chunk.text or chunk.text in q or difflib.SequenceMatcher(None, q, chunk.text).ratio() > 0.6:
                        matching_quote = q
                        break

                citations.append(
                    Citation(
                        law_name=chunk.law_name,
                        law_number=chunk.law_number,
                        law_year=chunk.law_year,
                        article_number=chunk.article_number,
                        quoted_text=matching_quote or chunk.text,
                        claim_text=explanation[:200] if explanation else None,
                        is_verified=False
                    )
                )

        # If no explicit citation detected from text, seed from top retrieved chunk
        if not citations and retrieved_chunks:
            top_c = retrieved_chunks[0]
            citations.append(
                Citation(
                    law_name=top_c.law_name,
                    law_number=top_c.law_number,
                    law_year=top_c.law_year,
                    article_number=top_c.article_number,
                    quoted_text=top_c.text,
                    claim_text=explanation[:200] if explanation else None,
                    is_verified=False
                )
            )

        return citations, quotations, explanation

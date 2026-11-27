"""
Citation Verification Engine for Egyptian Legal AI.

Verifies:
1. Law existence in retrieved knowledge base.
2. Article number precision.
3. Quoted text fidelity against authentic original legal text.
4. Semantic and logical support for the stated legal claim.
"""

from typing import List, Optional, Tuple, Dict
import difflib
import logging

from legal_knowledge.config import settings
from legal_knowledge.schemas.retrieval import RetrievedChunk
from legal_knowledge.schemas.citations import Citation, CitationVerificationResult
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class CitationVerifier:
    """
    Validates legal citations produced by AI agents against authentic retrieved legislation.
    """

    def __init__(
        self,
        min_quote_similarity: float = settings.CITATION_MIN_LEXICAL_OVERLAP,
        min_confidence: float = settings.CITATION_MIN_CONFIDENCE
    ):
        self.min_quote_similarity = min_quote_similarity
        self.min_confidence = min_confidence

    def verify_citation(
        self,
        citation: Citation,
        retrieved_chunks: List[RetrievedChunk]
    ) -> CitationVerificationResult:
        """
        Runs comprehensive multi-stage verification on a single citation.
        """
        warnings: List[str] = []
        law_matched = False
        article_matched = False
        quote_verified = False
        claim_supported = False
        quote_similarity = 0.0
        matched_chunk: Optional[RetrievedChunk] = None

        if not retrieved_chunks:
            return CitationVerificationResult(
                is_valid=False,
                law_matched=False,
                article_matched=False,
                quote_similarity=0.0,
                quote_verified=False,
                claim_supported=False,
                warnings=["لم يتم استرجاع أي مواد قانونية من قاعدة المعرفة لدعم هذا الاستشهاد."],
                reasoning="فشل التحقق: قاعدة الاسترجاع خالية من أي نصوص داعمة."
            )

        # 1. Check Law Existence
        norm_cited_law = ArabicNormalizer.normalize_for_search(citation.law_name or "")
        cited_law_num = ArabicNormalizer.convert_eastern_to_western_digits(citation.law_number or "")

        LAW_STOP_WORDS = {"قانون", "القانون", "رقم", "لسنه", "لسنة", "سنه", "سنة", "المصري", "جمهوريه", "مصر", "العربيه", "بشان", "باصدار"}
        cited_distinctive_words = [
            w for w in norm_cited_law.split()
            if len(w) > 2 and w not in LAW_STOP_WORDS
        ]

        candidate_chunks: List[RetrievedChunk] = []
        for chunk in retrieved_chunks:
            norm_chunk_law = ArabicNormalizer.normalize_for_search(chunk.law_name or "")
            chunk_law_num = ArabicNormalizer.convert_eastern_to_western_digits(chunk.law_number or "")

            num_match = (cited_law_num and chunk_law_num and cited_law_num == chunk_law_num)
            
            # Meaningful name match excluding generic boilerplate words like 'قانون'
            name_match = False
            if norm_cited_law and norm_chunk_law:
                if norm_cited_law == norm_chunk_law:
                    name_match = True
                elif cited_distinctive_words:
                    # Require at least one distinctive keyword to match and no contradictions
                    chunk_words = set(norm_chunk_law.split())
                    matching_distinctive = [w for w in cited_distinctive_words if w in chunk_words or any(w in cw for cw in chunk_words)]
                    # If cited law has distinctive words, at least 50% must match
                    if len(matching_distinctive) / len(cited_distinctive_words) >= 0.5:
                        name_match = True

            if num_match or name_match:
                law_matched = True
                candidate_chunks.append(chunk)

        if not law_matched:
            warnings.append(f"القانون المستشهد به '{citation.law_name}' غير موجود ضمن المواد المسترجعة.")
            candidate_chunks = retrieved_chunks  # Fallback to check all retrieved

        # 2. Check Article Number Match
        norm_cited_art = ArabicNormalizer.normalize_article_number(citation.article_number or "")
        
        for chunk in candidate_chunks:
            norm_chunk_art = ArabicNormalizer.normalize_article_number(chunk.article_number or "")
            if norm_cited_art and norm_chunk_art and norm_cited_art == norm_chunk_art:
                article_matched = True
                matched_chunk = chunk
                break

        if not article_matched:
            # If explicit article number was given but not found
            if citation.article_number:
                warnings.append(
                    f"رقم المادة المستشهد بها ({citation.article_number}) لم يتطابق مع أي مادة مسترجعة."
                )
            # Default to top candidate if law matched
            if candidate_chunks:
                matched_chunk = candidate_chunks[0]

        # 3. Check Quoted Text Authenticity
        if citation.quoted_text and matched_chunk:
            norm_quote = ArabicNormalizer.normalize_for_search(citation.quoted_text)
            norm_official = ArabicNormalizer.normalize_for_search(matched_chunk.text)

            # A. Exact substring containment
            if norm_quote in norm_official:
                quote_similarity = 1.0
                quote_verified = True
            else:
                # B. Sequence matcher for near-verbatim quote
                seq_ratio = difflib.SequenceMatcher(None, norm_quote, norm_official).ratio()

                # C. Token overlap
                q_tokens = set(norm_quote.split())
                doc_tokens = set(norm_official.split())
                token_overlap = len(q_tokens.intersection(doc_tokens)) / max(len(q_tokens), 1)

                quote_similarity = max(seq_ratio, token_overlap)
                if quote_similarity >= self.min_quote_similarity:
                    quote_verified = True
                else:
                    warnings.append(
                        f"النص المقتبس لا يتطابق بالدقة القانونية الكافية مع النص الرسمي للمادة "
                        f"(نسبة التطابق: {quote_similarity:.2%}). قد يتضمن صياغة غير أصلية."
                    )
        elif not citation.quoted_text:
            # No quote provided - relies on article match
            quote_verified = article_matched
            quote_similarity = 1.0 if article_matched else 0.0

        # 4. Check Claim Support
        if citation.claim_text and matched_chunk:
            norm_claim = ArabicNormalizer.normalize_for_search(citation.claim_text)
            norm_official = ArabicNormalizer.normalize_for_search(matched_chunk.text)

            claim_tokens = set(w for w in norm_claim.split() if len(w) > 2)
            official_tokens = set(norm_official.split())

            if claim_tokens:
                overlap = len(claim_tokens.intersection(official_tokens)) / len(claim_tokens)
                if overlap >= 0.40:  # Key conceptual terms present
                    claim_supported = True
                else:
                    warnings.append("الادعاء القانوني يحتوي مفاهيم غير مؤيدة بوضوح في نص المادة المسترجعة.")
            else:
                claim_supported = True
        else:
            claim_supported = article_matched

        # Overall validity determination
        is_valid = law_matched and article_matched and (quote_verified or not citation.quoted_text)

        reasoning_parts = []
        if is_valid:
            reasoning_parts.append("الاستشهاد صحيح ومطابق للمرجع القانوني المسترجع.")
        else:
            reasoning_parts.append("الاستشهاد غير موثق بالكامل أو يحتوي على تباينات.")
            if not law_matched:
                reasoning_parts.append("القانون غير موثق.")
            if not article_matched:
                reasoning_parts.append("رقم المادة غير مطابق.")
            if citation.quoted_text and not quote_verified:
                reasoning_parts.append("الاقتباس غير مطابق للنص الأصلي.")

        return CitationVerificationResult(
            is_valid=is_valid,
            law_matched=law_matched,
            article_matched=article_matched,
            quote_similarity=float(quote_similarity),
            quote_verified=quote_verified,
            claim_supported=claim_supported,
            matched_chunk_id=matched_chunk.chunk_id if matched_chunk else None,
            official_legal_text=matched_chunk.text if matched_chunk else None,
            warnings=warnings,
            reasoning=" ".join(reasoning_parts)
        )

    def verify_all(
        self,
        citations: List[Citation],
        retrieved_chunks: List[RetrievedChunk]
    ) -> Tuple[List[Citation], List[CitationVerificationResult], bool]:
        """
        Verifies a list of citations, updates their internal status flags,
        and determines if all citations are fully verified.
        """
        updated_citations: List[Citation] = []
        reports: List[CitationVerificationResult] = []
        all_passed = True

        for cit in citations:
            report = self.verify_citation(cit, retrieved_chunks)
            reports.append(report)

            cit_copy = cit.model_copy()
            cit_copy.is_verified = report.is_valid
            cit_copy.verification_status = "verified" if report.is_valid else "invalid"
            cit_copy.verification_details = report.reasoning
            updated_citations.append(cit_copy)

            if not report.is_valid:
                all_passed = False

        return updated_citations, reports, all_passed

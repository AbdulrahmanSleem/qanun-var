"""
Legal Q&A Evaluation: Citation Accuracy, Faithfulness, and Abstention Correctness.
"""

from typing import List
import difflib
from legal_knowledge.schemas.agent import AgentResult
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer


def evaluate_citation_accuracy(result: AgentResult) -> float:
    """
    Computes ratio of citations verified successfully.
    """
    if not result.citations:
        # If agent abstained legitimately, return 1.0, otherwise 0.0
        return 1.0 if result.status == "abstained" else 0.0

    verified_count = sum(1 for c in result.citations if c.is_verified)
    return verified_count / len(result.citations)


def evaluate_faithfulness(result: AgentResult, ground_truth_text: str) -> float:
    """
    Computes token-level semantic coverage between agent explanation and ground truth legal provision.
    """
    if result.status == "abstained":
        return 1.0

    norm_answer = ArabicNormalizer.normalize_for_search(result.legal_explanation or result.answer)
    norm_truth = ArabicNormalizer.normalize_for_search(ground_truth_text)

    ans_tokens = set(norm_answer.split())
    truth_tokens = set(norm_truth.split())

    if not truth_tokens:
        return 0.0

    overlap = len(ans_tokens.intersection(truth_tokens)) / len(truth_tokens)
    seq_ratio = difflib.SequenceMatcher(None, norm_answer, norm_truth).ratio()

    return max(overlap, seq_ratio)

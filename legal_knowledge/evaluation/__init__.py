"""
Evaluation module exports.
"""

from legal_knowledge.evaluation.dataset import BENCHMARK_DATASET, LegalEvaluationItem
from legal_knowledge.evaluation.retrieval_metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
)
from legal_knowledge.evaluation.qa_evaluation import (
    evaluate_citation_accuracy,
    evaluate_faithfulness,
)

__all__ = [
    "BENCHMARK_DATASET",
    "LegalEvaluationItem",
    "calculate_recall_at_k",
    "calculate_precision_at_k",
    "calculate_mrr",
    "evaluate_citation_accuracy",
    "evaluate_faithfulness",
]

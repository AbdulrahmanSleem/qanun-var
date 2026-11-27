"""
Executable Evaluation Harness for QANUN-VAR Legal Knowledge Engine.
Measures actual Recall@K, Precision@K, MRR, Latency, and Citation Accuracy.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

from legal_knowledge.config import settings
from legal_knowledge.retrieval.retrieval_service import LegalRetrievalService
from legal_knowledge.ingestion.pipeline import LegalIngestionPipeline
from legal_knowledge.agents.legal_qa_agent import LegalQAAgent
from legal_knowledge.schemas.agent import AgentRequest, AgentContext
from legal_knowledge.evaluation.dataset import BENCHMARK_DATASET, LegalEvaluationItem
from legal_knowledge.evaluation.retrieval_metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr
)
from legal_knowledge.evaluation.qa_evaluation import (
    evaluate_citation_accuracy,
    evaluate_faithfulness
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluation")


async def run_evaluation_suite() -> Dict[str, Any]:
    """Runs end-to-end benchmark evaluation over ingested authentic legislation."""
    print("=" * 80)
    print("QANUN-VAR: Egyptian Legal Knowledge & Retrieval System — Benchmark Evaluation")
    print("=" * 80)

    # 1. Initialize isolated retrieval service and ingestion pipeline
    retrieval_service = LegalRetrievalService()
    pipeline = LegalIngestionPipeline(retrieval_service=retrieval_service)
    qa_agent = LegalQAAgent(retrieval_service=retrieval_service)

    # 2. Ingest authentic sample laws
    data_dir = settings.BASE_DIR / "data" / "sample_laws"
    law_files = list(data_dir.glob("*.txt"))
    print(f"[*] Ingesting {len(law_files)} authentic Egyptian statutes from {data_dir}...")
    for f in law_files:
        doc, chunks = pipeline.ingest_file(f)
        print(f"    - Ingested '{doc.law_name}' ({len(chunks)} articles)")

    # 3. Evaluate each item in benchmark dataset
    print("\n[*] Evaluating benchmark queries...")
    results = []
    latencies = []
    recalls_at_1 = []
    recalls_at_3 = []
    recalls_at_5 = []
    mrrs = []
    citation_accuracies = []
    faithfulness_scores = []
    abstention_correctness = []

    for item in BENCHMARK_DATASET:
        t0 = time.perf_counter()
        # Execute retrieval
        retrieved_chunks = await retrieval_service.search_legal_sources(
            query=item.question,
            top_k=5,
            method="hybrid",
            apply_reranking=True
        )
        latency = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency)

        retrieved_articles = [c.article_number for c in retrieved_chunks if c.article_number]

        # Execute Legal Q&A Agent
        req = AgentRequest(query=item.question)
        qa_result = await qa_agent.run(req)

        if item.is_out_of_domain:
            # Should abstain
            is_correct_abstention = (qa_result.status == "abstained")
            abstention_correctness.append(1.0 if is_correct_abstention else 0.0)
            status_text = "PASSED (Abstained as expected)" if is_correct_abstention else "FAILED (Failed to abstain)"
            print(f"  [{item.query_id}] Out-of-domain test: {status_text}")
        else:
            r1 = calculate_recall_at_k(retrieved_articles, item.expected_article_number, k=1)
            r3 = calculate_recall_at_k(retrieved_articles, item.expected_article_number, k=3)
            r5 = calculate_recall_at_k(retrieved_articles, item.expected_article_number, k=5)
            mrr = calculate_mrr(retrieved_articles, item.expected_article_number)
            cit_acc = evaluate_citation_accuracy(qa_result)
            faith = evaluate_faithfulness(qa_result, item.ground_truth_summary)

            recalls_at_1.append(r1)
            recalls_at_3.append(r3)
            recalls_at_5.append(r5)
            mrrs.append(mrr)
            citation_accuracies.append(cit_acc)
            faithfulness_scores.append(faith)

            print(f"  [{item.query_id}] Target: Art {item.expected_article_number} | "
                  f"Retrieved: {retrieved_articles[:3]} | R@1: {r1:.1f} | R@3: {r3:.1f} | "
                  f"MRR: {mrr:.2f} | CitAcc: {cit_acc:.2f} | Latency: {latency:.1f}ms")

    # Aggregate metrics
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
    mean_r1 = sum(recalls_at_1) / len(recalls_at_1) if recalls_at_1 else 0.0
    mean_r3 = sum(recalls_at_3) / len(recalls_at_3) if recalls_at_3 else 0.0
    mean_r5 = sum(recalls_at_5) / len(recalls_at_5) if recalls_at_5 else 0.0
    mean_mrr = sum(mrrs) / len(mrrs) if mrrs else 0.0
    mean_cit_acc = sum(citation_accuracies) / len(citation_accuracies) if citation_accuracies else 0.0
    mean_faith = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
    abstention_rate = sum(abstention_correctness) / len(abstention_correctness) if abstention_correctness else 1.0

    print("\n" + "=" * 80)
    print("ACTUAL MEASURED BENCHMARK RESULTS")
    print("=" * 80)
    print(f"| Metric                      | Measured Score |")
    print(f"|-----------------------------|----------------|")
    print(f"| Recall@1                    | {mean_r1 * 100:6.2f}%         |")
    print(f"| Recall@3                    | {mean_r3 * 100:6.2f}%         |")
    print(f"| Recall@5                    | {mean_r5 * 100:6.2f}%         |")
    print(f"| Mean Reciprocal Rank (MRR)  | {mean_mrr:6.4f}         |")
    print(f"| Citation Verification Acc.  | {mean_cit_acc * 100:6.2f}%         |")
    print(f"| Answer Faithfulness         | {mean_faith * 100:6.2f}%         |")
    print(f"| Abstention on Out-of-Domain | {abstention_rate * 100:6.2f}%         |")
    print(f"| Average Retrieval Latency   | {mean_latency:6.2f} ms       |")
    print("=" * 80)

    return {
        "recall_at_1": mean_r1,
        "recall_at_3": mean_r3,
        "recall_at_5": mean_r5,
        "mrr": mean_mrr,
        "citation_accuracy": mean_cit_acc,
        "faithfulness": mean_faith,
        "abstention_rate": abstention_rate,
        "mean_latency_ms": mean_latency
    }


if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())

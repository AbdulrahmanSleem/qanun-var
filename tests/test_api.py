"""
Tests for FastAPI Service Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from legal_knowledge.api.app import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "QANUN-VAR" in data["service"]


def test_api_retrieve():
    payload = {
        "query": "العقد شريعة المتعاقدين",
        "top_k": 3,
        "method": "hybrid",
        "apply_reranking": True
    }
    response = client.post("/api/v1/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "results" in data
    assert "latency_ms" in data


def test_api_qa():
    payload = {
        "query": "ما هو حكم تعديل العقد بإرادة منفردة طبقاً للقانون المدني المصري؟"
    }
    response = client.post("/api/v1/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["answered", "abstained"]
    assert "answer" in data
    assert "disclaimer" in data


def test_api_verify_citation():
    payload = {
        "citation": {
            "law_name": "القانون المدني",
            "article_number": "147",
            "quoted_text": "العقد شريعة المتعاقدين"
        },
        "retrieved_chunks": [
            {
                "chunk_id": "chunk_147",
                "text": "العقد شريعة المتعاقدين، فلا يجوز نقضه ولا تعديله إلا باتفاق الطرفين.",
                "law_name": "القانون المدني",
                "article_number": "147"
            }
        ]
    }
    response = client.post("/api/v1/verify-citation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["law_matched"] is True
    assert data["article_matched"] is True

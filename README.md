
# QANUN-VAR

Intelligent Arabic legal assistant for Egyptian lawyers and startups (DEPI Agentic & Gen AI track).
Four features — Legal Q&A with citations, Contract Review, Case Analysis, Contract Generation —
coordinated by a LangGraph Orchestrator over a shared, source-grounded legal knowledge base.

## Repo rules (all members)
1. `main` is protected. Work on feature branches, merge via peer-reviewed PR.
2. Import shared services ONLY: LLM from `shared/llm_service.py`, search from
   `shared/retrieval_service.py`, file parsing from `shared/document_service.py`.
3. Agents speak `shared/schemas.py` (AgentRequest -> AgentResponse) via `run_agent`.
4. Never send client/case data to free-tier APIs — public legal texts only.
5. Run `pytest` and `ruff check` before every PR.

## Quick start
```bash
cp .env.example .env   # fill in free-tier keys (Gemini, Groq, OpenRouter)
pip install -r requirements.txt
uvicorn api:app --reload        # API on :8000
streamlit run app.py            # UI on :8501
# or: docker-compose up --build
```

## Sprint gates
| Day | Gate |
|-----|------|
| 2 | KB indexed + all 4 mock agents route end-to-end |
| 4 | Feature 1 end-to-end with Citation Verifier |
| 7 | All four features integrated |
| 9 | Evaluation report with failure cases |
| 10 | docker-compose delivery + defense readiness |

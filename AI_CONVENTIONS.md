
# QANUN-VAR — Team AI Usage Convention (the "common skill")

Why this exists: all 5 of us use AI coding tools, and uncoordinated AI use is
how repos end up with 5 code styles, duplicated logic, and merge conflicts.
These 10 rules keep AI output consistent and non-overlapping. Everyone
commits to this file with their first PR.

## 1. Ownership map — AI may only touch YOUR files
| Area | Owner | AI tools may edit |
|---|---|---|
| `shared/schemas.py`, `shared/llm_service.py`, `graph.py`, `docker-compose.yml` | Sleem | NOBODY's AI without lead PR review (FROZEN) |
| `shared/retrieval_service.py`, `ingestion_pipeline/`, `agents/legal_qa.py` | Ali | Ali's AI only |
| `shared/document_service.py`, `checklists/`, `agents/contract_review.py` | Mo3taz | Mo3taz's AI only |
| `agents/case_analysis.py`, `evaluation/` | Mowafy | Mowafy's AI only |
| `agents/contract_generation.py`, `templates/`, `app.py`, `api.py` | ElMelegy | ElMelegy's AI only |
If your task needs a change in someone else's area, open an ISSUE and tag them —
never let your AI tool edit it directly.

## 2. The one entry prompt (paste into your AI tool before ANY code work)
> You are working in the QANUN-VAR repo, an Arabic legal-assistant project.
> Rules: Python 3.11, pydantic v2, type hints, docstrings in English, user-facing
> text in Arabic. You may ONLY read/modify files I list below. You must NOT touch
> shared/schemas.py, shared/llm_service.py, graph.py, or any file owned by
> another workstream. Output: unified diff only, no rewrites of untouched code.

## 3. Always give the AI context before asking
Paste the relevant frozen interface (`shared/schemas.py` models) and the
service stubs into the chat first. AI that hasn't seen `AgentRequest`/`AgentResponse`
will invent its own shapes -> schema errors at integration.

## 4. AI output is a draft, not a deliverable
- You must be able to explain every line in standup. "The AI wrote it" is not an explanation.
- Never paste AI output straight to `main` branch of your PR — review the diff first.
- Run `pytest -q && ruff check .` locally before pushing, even if the AI says it passed.

## 5. Small PRs, one workstream per PR
Max ~300 lines changed per PR, one feature area per PR. AI generates big-bang
diffs by default — ask it to split the work: "first just the function signatures + tests".

## 6. No overlapping AI sessions on the same file
One member = one AI session editing a file at a time. If two of you ask AIs to
change `api.py` on the same day, you get unmergeable PRs. Check the task board first.

## 7. Prompt log discipline
Keep a short `notes/ai-log-<yourname>.md`: date, goal, prompt used, result kept/discarded.
At standup: "what did your AI do yesterday" becomes a 30-second read. Reusable good
prompts get promoted into this file's appendix by the lead.

## 8. Data & privacy red line for AI tools
Free-tier tools may train on what you paste. NEVER paste: client documents, real case
files, the `.env` file, API keys. Use public law texts and synthetic sample contracts only.

## 9. Shared vocabulary (use exact names so AIs stay consistent)
- Agent input/output: `AgentRequest` / `AgentResponse` / `VerifiedAnswer` / `Citation`
- LLM call: `shared.llm_service.generate(prompt)` — never call Gemini/Groq directly
- Search: `shared.retrieval_service.retrieve_articles(query, top_k, rerank_top_n)`
- Files: `document_service.extract()` / `confirm_text()`
If your AI invents new names for these, rename before committing.

## 10. Definition of Done (every task, no exceptions)
1. Code merged via PR with 1 peer review (not your own)
2. `pytest -q && ruff check .` green in CI
3. Demo evidence in the PR (screenshot / log / recording)
4. Task box checked in docs/TASKS.md in the same PR

---------------------------------------------------------------------------
## Appendix A — Approved prompt patterns (add good ones as we find them)
- Retrieval tuning: "Given these 5 retrieved Arabic articles and this question,
  judge relevance 0-1 and explain in one line." (eval helper)
- Checklist building: "For an Egyptian employment contract from the EMPLOYEE's
  side, list 8 risky clause patterns with the Labor Law article that governs each."
- Test data: "Generate 3 synthetic NDA contracts: one clean, one with a missing
  confidentiality-definition clause, one with an unbalanced penalty clause."

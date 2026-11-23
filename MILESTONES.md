
# QANUN-VAR — Milestone Playbook (per member, per gate)

Gates: **G1 Day 2** KB+skeleton | **G2 Day 4** F1 end-to-end | **G3 Day 7** all features |
**G4 Day 9** evaluation report | **G5 Day 10** delivery & defense.
Every task ends with a PR to `main`. Standup daily 15 min: yesterday / today / blockers.
Frozen files (`shared/`, `graph.py`, `docker-compose.yml`) need lead review.

---------------------------------------------------------------------------
## GATE 1 — Day 2: Knowledge Base & Skeleton Ready
Acceptance: Civil + Labor laws indexed at article level in ChromaDB; all 4 mock
agents route Streamlit -> FastAPI -> LangGraph -> mock response.

| Who | Task | Done when |
|---|---|---|
| Ali | A-01 Collect both laws from official/public sources; log source URL + access date | Source manifest committed to `data/SOURCES.md` |
| Ali | A-02 Verify article counts vs official text (~1,149 Civil / ~257 Labor) | Count table in SOURCES.md; discrepancies noted |
| Ali | A-03 Arabic normalizer + article-level chunker with metadata | Unit test on 20 sample articles passes |
| Ali | A-05 Index into ChromaDB (BGE-M3 embeddings + BM25 side index) | Index persisted under `data/indexed/` |
| Sleem | S-03 Intent classifier in `graph.py` (rule-based + LLM fallback) | 10 sample prompts classified correctly |
| Sleem | S-04 Hybrid retrieval skeleton wired to Ali's store | `retrieve_articles()` returns articles (may be rough) |
| Mo3taz | M-01 `extract()` for PDF/DOCX/TXT (OCR can wait) | 3 sample contracts extract cleanly |
| Mowafy | F-05 Start eval datasets: 25 of the 50 Q&A reference answers written | `evaluation/test_datasets/qa_reference.jsonl` |
| ElMelegy | E-01 Streamlit sidebar: 4 intents call API and render response | Screen recording or screenshot in PR |
| All | Standup end of Day 2 — gate demo: ask mock question in UI, get routed mock answer | G1 PASS/FAIL recorded in README |

---------------------------------------------------------------------------
## GATE 2 — Day 4: Feature 1 Working End-to-End
Acceptance: Arabic legal question -> answer with exact law/article -> deterministic
Citation Verifier passes (or refusal when unsupported).

| Who | Task | Done when |
|---|---|---|
| Ali | A-06 Retrieval smoke test: 20 benchmark Qs, correct article in top-5 >= 80% | `evaluation/retrieval_smoke.md` with numbers |
| Ali | A-07 Deterministic Citation Verifier (every cited article exists in retrieved passages) | Unit tests: pass case + fabricated-citation case |
| Ali | A-08 `legal_qa_agent` full loop: rewrite -> retrieve -> generate-from-sources -> verify -> refuse-if-unsupported | Demo Qs answered with article text quoted |
| Sleem | S-05 Wire verifier into `graph.py`; block failed responses with notes | Verifier failure visible in API response |
| Sleem | S-06 Failover drill: force Gemini error, confirm Groq answers; log provider per request | Log excerpt in PR |
| Mo3taz | M-02 OCR + human-confirmation flow (scans set `needs_human_confirmation`, confirm endpoint) | Upload scan -> confirm text -> proceed, demo'd |
| Mowafy | F-05 Finish: 50 Q&A reference answers + 15 labeled contracts started | Datasets committed |
| ElMelegy | E-02 Upload flow in UI: preview extracted text, edit box, confirm, submit | Demo in PR |
| All | G2 demo Day 4: 3 live Arabic questions, at least 1 verifier refusal shown | G2 PASS/FAIL in README |

---------------------------------------------------------------------------
## GATE 3 — Day 7: All Four Features Integrated
Acceptance: F1-F4 (incl. OCR preview and DOCX download) work end-to-end through
the Orchestrator with no schema errors.

| Who | Task | Done when |
|---|---|---|
| Ali | Support F2/F3 retrieval queries (filters by law type if needed) | F2/F3 retrieval calls return relevant articles |
| Mo3taz | M-03 Clause segmentation + M-04 contract type detection (3 MVP types) | Segmented clauses shown for sample contracts |
| Mo3taz | M-05 Legal specialist session ~Day 3 output: risk checklists per MVP type finalized | `checklists/*.md` signed off, committed |
| Mo3taz | M-06 Risk scoring High/Med/Low + missing clauses + alternative wording; M-07 graceful-degradation API for F4 | Sample report renders in UI |
| Mowafy | F-01/F-02 30-50 rulings curated + indexed; F-03 case agent: facts/parties/issues + strengths/weaknesses each linked to a legal basis | Case summary demo on 2 sample cases |
| Mowafy | F-04 Outcome range (likely/unlikely/undetermined) + reasons + non-binding disclaimer in EVERY output | Disclaimer string verified in tests |
| ElMelegy | E-03 Questionnaires for 3 MVP types; E-04 Jinja2+python-docx Arabic DOCX with RTL + download | Generated DOCX opens correctly in Word |
| ElMelegy | E-05 F4 -> F2 self-review wiring with degradation flag | Review summary shown under generated contract |
| Sleem | Integration sweeps Day 5-7: fix schema mismatches, run full docker-compose | `docker-compose up` runs all 4 features |
| All | G3 demo Day 7: one full pass of each feature live | G3 PASS/FAIL in README |

---------------------------------------------------------------------------
## GATE 4 — Day 9: Evaluation Report Complete
Acceptance: quantitative metrics documented with failure cases and applied fixes.

| Who | Task | Done when |
|---|---|---|
| Mowafy | F-06 Legal specialist reviews sample of test Qs + labels (~Day 6) | Review notes committed |
| Mowafy | F-07 Run all metrics: retrieval accuracy, Ragas faithfulness, refusal rate, risk recall/precision, latency | `evaluation/results.json` |
| Mowafy | F-08 `evaluation_report.md`: metrics + failure cases + fixes applied | Report merged to main |
| Ali | F1 metrics support: log retrieval ranks for eval Qs | Rank log in results |
| Mo3taz | F2 metrics support: risk label comparison script | Precision/recall numbers in results |
| Sleem | System metrics: latency per request, provider usage counts (free-tier), docker-compose uptime | Tracing summary in results |
| ElMelegy | Pilot survey drafted for lawyers/startups (post-defense feedback form) | Form link in report appendix |
| All | Day 9 standup: report walkthrough, choose which failure cases go in slides | G4 PASS |

---------------------------------------------------------------------------
## GATE 5 — Day 10: Final Delivery & Defense Readiness
Acceptance: docker-compose reliable, repo clean, slides + demo script finalized.

| Who | Task | Done when |
|---|---|---|
| Sleem | S-07 Final compose test on a clean machine/profile; S-08 tag `v1.0-defense`, protect main | Tag pushed, fresh `up` works |
| Sleem | Record backup demo video (all 4 features, 5 min) | Video link in README |
| ElMelegy | E-08 UI polish: Arabic labels, disclaimer every page, defense demo script | Demo script rehearsed once end-to-end |
| Mowafy | Slides: problem, architecture, metrics, failure cases, future work | Slides PDF in repo `docs/` |
| Ali | KB docs: SOURCES.md final, amendment-date warning verified | Warning shown on an amended-article demo |
| Mo3taz | OCR confidence demo + human-confirmation guardrail in the demo script | Included in slides |
| All | Full defense rehearsal Day 10 morning; freeze code at noon | G5 PASS |

---------------------------------------------------------------------------
## Dependency map (who blocks whom)
S-05 <- A-07 | E-05 <- M-07 | F-03/F-04 <- A-05 (retrieval) | F2 checklists <- legal specialist (M-05)
Rule: if a dependency slips, integrate with a mock and mark `status="degraded"` — gates never wait.

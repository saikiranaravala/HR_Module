# Deep-Dive PRD 14 — AI-Native Capability Layer
*Project Meridian | Platform layer | Governs and powers every AI feature in modules 01–11*

## 1. Mission & Success Metrics
One governed AI platform — gateway, retrieval, agents, evaluation — so every module ships intelligence quickly without each team re-solving safety, compliance, or quality.
- Groundedness: ≥ 98% of copilot answers cite governing source; hallucinated-policy incidents: 0 tolerated (sev-1 class).
- Deflection ≥ 30% (10-ESS), payroll anomaly precision ≥ 80% at review-queue volume ≤ 2% of records.
- Governance: 100% of AI use cases registered + risk-classified before prod; quarterly adverse-impact tests on all evaluative features, on time.

## 2. AI Gateway (P0)
Single egress for all model calls: model abstraction (Claude family primary — Opus-class for complex reasoning/agents, Haiku-class for classification/extraction at volume; provider-pluggable behind one interface), prompt registry (versioned, reviewed, env-promoted like config per 12-PLAT), per-use-case budgets (cost + latency SLOs with circuit breakers), PII handling (field-level redaction/tokenization policies per use case; re-identification post-response where authorized), zero-retention + no-training contractual posture with providers, full audit store (request/response/model-version/prompt-version/user/purpose — the AI ledger, retention per legal), regional routing honoring TECH-10 residency.

## 3. Knowledge & Retrieval Service (P0)
Corpus: policies/handbooks (country/population variants), CBAs, benefits plan docs (SPDs), process guides, KB articles (10-ESS authored). **Architecture: hierarchical index-tree, vectorless-first retrieval** — the corpus is structured, modestly sized, regenerated on every policy release, and variant-safety-critical; tree navigation by (country → population → topic) with LLM-guided traversal gives deterministic scoping that embedding similarity cannot guarantee (a DE worker must never receive a US FMLA answer). Embedding search runs as secondary recall within the already-scoped branch only. Document lifecycle: ingestion on publish events from KB/document systems, version pinning (answers cite doc version + effective date), staleness flags surfacing to content owners, deleted-doc tombstoning (immediate retrieval exclusion). Personal-context grounding: copilot composes corpus answers with the worker's own data (balances, elections, country) fetched under the *worker's own* authorization scope — the AI can never see more than the asking user could.

## 4. Agent Framework (P0)
LangGraph orchestration: typed tool contracts onto Meridian APIs (tools inherit caller's RBAC scope — no privileged service accounts for user-facing agents), mandatory human-approval gates on state changes touching money/employment status/access (agent drafts the transaction; human commits — enforced at API capability level, not prompt level), step-level audit (every tool call in the AI ledger), per-agent kill switch + feature flags (regional, per master AI governance), sandboxed evaluation harness (agents tested against synthetic tenant before promotion).
Launch agents: ESS HR copilot (10), payroll anomaly explainer (03), HR case assist (10), manager copilot (07/01), data-quality agent (P2, AI-10).

## 5. Use-Case Specifications (cross-module registry excerpt)
| Use case | Module | Risk class (EU AI Act lens) | Human role |
|---|---|---|---|
| Policy Q&A copilot | 10 | Limited (transparency duty) | Self-serve; escalation path |
| Payroll anomaly scoring | 03 | Limited/internal control | Reviewer disposition required |
| Resume rank-and-explain | 06 | **High-risk** (employment) | Recruiter decides; never auto-reject; LL144 audit |
| Review draft assist | 07 | Limited→monitored | Manager edits; AI never rates |
| Bias-language lint | 06/07 | Limited | Advisory only |
| Benefits decision support | 04 | Limited (non-advice framing) | Employee decides |
| Attrition risk (aggregate) | 11 | High-risk if individualized → aggregate-only y1 | HR strategic use only |
Each registry entry: purpose, data categories, model/prompt versions, evaluation results, DPIA link, works-council artifacts (where required), monitoring plan, owner.

## 6. Evaluation & Quality Engineering
Golden Q&A sets per country/population (built with HR SMEs; refreshed each policy release — regeneration of corpus triggers eval re-run automatically); groundedness/citation checks automated (answer-claims vs. cited source entailment); red-team suites (prompt injection via user text fields, data-exfiltration attempts, cross-population leakage probes) in CI; production monitoring: sampled human review queues, thumbs-down triage SLA, drift dashboards (deflection, escalation rate, topic-level accuracy); incident class definitions (hallucinated policy = sev-1 with comms runbook).

## 7. Governance Operations (P0)
AI review board (HR, legal, privacy, security, works-council liaison) gating registry entries; EU AI Act conformity workflow for high-risk entries (logging, oversight design docs, accuracy metrics); NYC LL144 annual independent bias audit logistics for screening tools; Colorado AI Act impact assessments; transparency: in-product "AI-generated" labels, employee-facing AI use disclosure page per jurisdiction, opt-out mechanics where mandated; training data posture: enterprise data never used for provider model training; internal fine-tuning (if ever) requires separate board approval + DPIA.

## 8. Edge Cases Register
Policy contradiction between CBA and handbook (retrieval returns both with precedence note + routes to case, never resolves silently); user pastes another worker's PII into copilot (detection → scope warning + non-processing of third-party data); answer correct at as-of date but policy changed yesterday (effective-date prominence + change-banner); injection text inside resumes/case descriptions (input hardening + tool-scope minimalism); model-provider outage (graceful degradation: copilot → search + KB links, agents pause cleanly).

## 9. Open Questions
On-prem/regional model options for highest-sensitivity flows (comp/succession summarization) vs. excluding those domains from AI year-one (recommend exclude y1). Voice interface for frontline workers (P2 spike — ties to existing voice-assistant patterns).

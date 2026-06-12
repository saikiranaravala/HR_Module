# Module 4 Design — AI-Native Capability Layer (Specs/14)

**Spec:** [Specs/14-ai-layer.md](../Specs/14-ai-layer.md) · **Package:** `src/ai_layer/` · Tests: `src/test/ai_layer/`

## 1. Scope & Requirement Trace

| Spec section | Design element | Local scope |
|---|---|---|
| §2 AI Gateway (P0) | `gateway.py` — single egress; provider-pluggable (`MockProvider` locally, Claude later via the same interface); versioned prompt registry (YAML); use-case registry with budgets + circuit breaker; PII guard; **AI ledger** table (request/response/model/prompt-version/user/purpose) | **Yes** |
| §3 Knowledge & Retrieval (P0) | `retrieval.py` — hierarchical index-tree, vectorless: country → population → topic traversal; version pinning; tombstoning; effective-date change banners; contradiction handling | **Yes** |
| §4 Agent framework (P0) | `agents.py` — typed tool contracts that call the platform policy engine with the CALLING USER's subject (no privileged accounts); human-approval gate: mutating tools on money/employment/access return drafts, never commit | **Yes** (LangGraph orchestration itself deferred — local agents are deterministic tool sequences) |
| §5 Use-case registry | `config/use_cases.yaml` — risk class, human role, budget | **Yes** |
| §6 Eval / §7 Governance ops | Golden Q&A runner piggybacks on rules_workflow golden pattern; board workflows deferred | Partial |

## 2. Key decisions

- **No real model calls locally.** The provider interface is final (`complete(prompt, model_class) -> Completion`); `MockProvider` returns deterministic responses for tests. Swapping in the Anthropic client touches one class.
- **Deterministic scoping beats similarity**: retrieval filters by (country, population) BEFORE topic matching — a DE worker can never receive a US-scoped document because the US branch is never traversed (spec §3's core safety property).
- **Approval gates live at the capability level, not the prompt level**: `ToolContract(mutates=GATED)` returns an `AgentDraft`; committing a draft is a separate human call that goes through the normal policy decision.
- **Every gateway call writes a ledger row** — including refused ones (budget breaker, PII guard) with the refusal reason.

## 3. Edge-Case Test Plan (register → named tests)

| Register row | Test |
|---|---|
| CBA vs handbook contradiction → both + precedence note | `test_AI_policy_contradiction_returns_both` |
| Cross-population leakage (DE worker / US FMLA) | `test_AI_cross_population_scoping_is_structural` |
| Third-party PII pasted into copilot | `test_AI_third_party_pii_not_processed` |
| Policy changed yesterday → change banner | `test_AI_effective_date_change_banner` |
| Injection text in user content | `test_AI_injection_text_flagged` |
| Model-provider outage → graceful degradation | `test_AI_provider_outage_degrades_gracefully` |

## Change Log

- **2026-06-10** — Initial design + implementation. Trigger: Module 4 kickoff (auto-approved cadence).

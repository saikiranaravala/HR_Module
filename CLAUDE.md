# CLAUDE.md — Project Meridian

Instructions for Claude (Claude Code and chat) when working in this repository. Read this before generating any code, schema, or document.

## Project Context

Meridian is an AI-native HCM platform replacing Oracle PeopleSoft for 50K+ global employees. All specs live in the `Specs/` folder: `Specs/PRD-Meridian-HCM.md` (master) and `Specs/01-*.md` … `Specs/16-*.md` (domain deep-dives, indexed in `Specs/00-INDEX.md`). **When implementing a feature, locate and cite the requirement ID (e.g., CORE-3, PAY-5) it satisfies. If no requirement covers the work, flag it — don't invent scope.**

Requirement IDs are *defined* in the master PRD (with P0/P1/P2 priority tags); domain PRDs expand them (e.g., `Specs/03-payroll-hub.md` §5 expands PAY-3). The master PRD is canonical for ID + priority; the domain PRD is canonical for detail. `Specs/00-INDEX.md` lists five cross-cutting decision dependencies (payroll RFP, ratings philosophy, ATS/LMS build-vs-buy, residency rulings, works-council inventory) — check whether your work area is gated by one before designing.

**Repository status:** specification phase complete; implementation proceeds **module by module**. Track and update `Progress.md` (root) for every unit of work — see "Progress Tracking" below. Durable decisions and learnings go in `.claude/memory.md`. Reusable workflows live in `.claude/skills/`.

## Repository Layout & Local Toolchain

| Path | Contents |
|---|---|
| `Specs/` | Immutable PRDs (master + 16 domain deep-dives) |
| `TechDesignDoc/` | Technical design docs, one per module (`NN-<module>-design.md`) — kept in sync with code via the `update-design-doc` skill |
| `src/` | Backend code, one Python package per bounded context (e.g., `src/platform_core/`) |
| `src/test/` | Tests, mirroring the package layout (`src/test/platform_core/`) |
| `UI/` | React frontend (npm/Vite) — scaffolded when the first UI-bearing module starts |
| `Progress.md` | Build tracker (root) |

**Pinned local toolchain (use these; don't assume cloud infra):** Python 3.11.9 (backend: FastAPI, SQLAlchemy 2.x, Alembic, pytest), Node v24.14.0 + npm 11.11.0 (UI only), PostgreSQL local instance (database `meridian`).

**Local deviations from spec (deliberate, recorded in `.claude/memory.md`):** the Kafka/Redis/OpenSearch backbone is not present — **events are deferred** (direct service calls for now; Invariant #7 re-enabled when the event layer module lands). Cloud-only concerns (EKS, multi-region DR, SIEM) are documented as N/A-local in design docs, never silently dropped.

## Progress Tracking (mandatory)

`Progress.md` at the repo root is the single source of truth for build status. Rules:
- Before starting work, check `Progress.md` for the current module and its status.
- After completing any meaningful unit (design doc, schema, service scaffold, tests, review), append a dated entry to the Progress Log and update the module's status row.
- Status values: `Not Started → Design → In Progress → Testing → Done`. A module is `Done` only when its PRD edge-case register is implemented as passing named tests.
- One module at a time; don't start a new module while another is `In Progress` unless the user directs it.

## Architecture Invariants (never violate; if a task seems to require it, stop and raise it)

1. **Temporal data is sacred.** Every person/job/comp/org entity uses the shared temporal pattern: `effective_date` + `effective_sequence` + action/reason + full audit capture. Never write "current state only" tables for these domains. All read APIs on temporal entities accept `as_of`. Retroactive changes must emit retro events — never silent rewrites.
2. **Bounded contexts own their schemas.** No cross-service database access. Cross-domain reads go through APIs or event-built read models. If you're tempted to join across service schemas, you're designing it wrong.
3. **One policy decision point.** All authorization (UI, API, reports, analytics, AI tool scopes) calls the central policy service. Never re-implement access logic locally. Never special-case a bypass. Sensitivity tiers: T0 internal-public, T1 person-standard, T2 comp/national-ID/banking, T3 health-adjacent/ER-cases/succession. T2/T3 reads are audit-logged.
4. **No provider/vendor codes upstream of adapters.** Payroll, carrier, and partner formats exist only inside the adapter layer (PRD 03/13). Everything upstream speaks the canonical contracts.
5. **Configuration-only extensibility.** Business logic variation goes in the rules engine (decision tables preferred) or workflow designer (PRD 12) — versioned, effective-dated, testable. Do NOT add server-side scripting hooks, code forks, or per-customer branches. This is the anti-PeopleCode rule; it is load-bearing.
6. **AI is governed.** All model calls route through the AI Gateway. Agents inherit the *calling user's* scope — no privileged service accounts for user-facing AI. Agents draft; humans commit anything touching money, employment status, or access. Retrieval is population-scoped (country/union/grade) — a worker must never receive another population's policy answer. AI never assigns or recommends performance ratings, and never auto-rejects candidates.
7. **Events are contracts.** CloudEvents envelope, schema-registry validated, backward-compatible minor changes only, PII-minimized payloads (IDs + change type; consumers pull detail under their own scopes). All consumers must be idempotent.
8. **Privacy by construction.** Every new field gets catalog tags (category, purpose, lawful basis, retention class) at schema time. National IDs and bank details use field-level envelope encryption. No production data below prod — synthetic/masked only.

## Tech Stack & Conventions

- **Backend:** services per bounded context; PostgreSQL (Aurora) per service; Kafka (MSK); Redis (no PII); OpenSearch (security-trimmed indexing). Prefer boring, proven patterns over novelty.
- **APIs:** REST per OpenAPI 3.1, `/v{n}` versioning, cursor pagination, idempotency keys on mutations, RFC7807 errors, correlation-ID propagation end-to-end. GraphQL read-only with persisted queries.
- **Frontend:** shared design system; web + native iOS/Android; WCAG 2.2 AA is a CI gate, not an afterthought; all strings externalized for localization from day one.
- **AI:** Claude via AI Gateway only (Opus-class for reasoning/agents, Haiku-class for high-volume classification). LangGraph for agents with typed tool contracts. Prompts live in the versioned prompt registry, not inline in code.
- **Infra:** Terraform + OPA policy-as-code, GitOps (ArgoCD), mTLS service mesh, signed images + SBOM.

## Testing Requirements (PRs without these are incomplete)

- Temporal correctness tests for any effective-dated entity (as-of queries, sequence conflicts, retro events) — use the shared temporal conformance suite.
- Rules/workflow changes ship with decision-table unit tests + golden-dataset regression runs (the TIME simulator pattern); 100% pass gates promotion.
- Edge-case registers in each PRD's penultimate section are **mandatory test scenarios** for that domain — implement them as named tests (e.g., `test_PAY_negative_net_arrears`).
- Cross-surface security consistency: anything reachable via report/API/AI must be denied identically when the UI denies it — covered by the policy consistency suite.
- Payroll-path code additionally requires: reconciliation identity tests (original + retro delta = recalculated) and snapshot immutability tests.

## Working Style for Claude

- **Cite requirement IDs** in PR descriptions, commit messages, and design docs.
- **Surface conflicts, don't resolve them silently.** If two PRDs disagree, or a request violates an invariant, say so explicitly and propose options.
- When generating schemas/DDL: include effective-dating columns, audit columns (`created_by`, `created_at`, `source_channel`, correlation id), and catalog tags as comments.
- When generating sample/test data: synthetic only — realistic shapes, zero real-looking national IDs or bank numbers (use reserved/invalid ranges).
- Country-specific logic goes in country packs (versioned config/content), never hardcoded conditionals like `if country == 'DE'` in service code.
- Documents follow the PRD house style: mission + metrics, requirements with acceptance criteria, data model, workflows, events/APIs, edge-case register, open questions.
- Keep responses and docs dense and concrete; prefer tables for catalogs/matrices, prose for rationale.

## Do-Not List

- Don't bypass the AI Gateway, policy service, or adapter layer "temporarily."
- Don't store PII in Redis, logs, events payloads, or analytics without tokenization.
- Don't write migration scripts that mutate history without retro events and reconciliation evidence.
- Don't add dependencies to the payroll pipeline that introduce silent-failure modes — the pipeline halts loudly or proceeds provably; it never degrades quietly.
- Don't create per-country code branches, scripting hooks, or schema forks.

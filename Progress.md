# Project Meridian — Build Progress

Single source of truth for module-by-module build status. Updated after **every** unit of work (design doc, schema, slice, tests). See the `update-progress` skill in `.claude/skills/` for the entry format and status rules.

**Status legend:** `Not Started` → `Design` → `In Progress` → `Testing` → `Done`
A module is `Done` only when its PRD Edge Cases Register is fully covered by passing named tests.

**Execution rule:** one module at a time, in build-order below, unless the user directs otherwise.

## Module Status

Build order follows the phase anchors in [Specs/00-INDEX.md](Specs/00-INDEX.md): platform foundations first, then Core HR, then the operational core, then the talent suite. Migration (16) runs program-long alongside.

| # | Module | Spec | Phase | Status | Design Doc | Edge-Case Tests |
|---|--------|------|-------|--------|------------|-----------------|
| 1 | Tech, Security & Privacy foundation | [Specs/15](Specs/15-technical-architecture.md) | Foundation (P0) | Testing (awaiting review) | [TechDesignDoc/15](TechDesignDoc/15-foundation-design.md) | 3/3 local passing, 3 deferred N/A-local |
| 2 | Workflow, Rules & Extensibility | [Specs/12](Specs/12-platform.md) | Foundation (P0) | Not Started | — | — |
| 3 | Integration Architecture | [Specs/13](Specs/13-integration.md) | Foundation (P0) | Not Started | — | — |
| 4 | AI-Native Capability Layer | [Specs/14](Specs/14-ai-layer.md) | Foundation (P0) | Not Started | — | — |
| 5 | Core HR & Workforce Administration | [Specs/01](Specs/01-core-hr.md) | Foundation (P0) | Not Started | — | — |
| 6 | Time & Labor + Absence | [Specs/02](Specs/02-time-labor.md) | Operational core (P0) | Not Started | — | — |
| 7 | Payroll Integration Hub | [Specs/03](Specs/03-payroll-hub.md) | Operational core (P0) | Not Started | — | — |
| 8 | Benefits Administration | [Specs/04](Specs/04-benefits.md) | Operational core (P0) | Not Started | — | — |
| 9 | ESS/MSS + HR Service Delivery | [Specs/10](Specs/10-ess-mss.md) | Operational core (P0) | Not Started | — | — |
| 10 | Workforce Analytics & Reporting | [Specs/11](Specs/11-analytics.md) | Foundation→P1 | Not Started | — | — |
| 11 | Compensation Planning | [Specs/05](Specs/05-compensation.md) | Talent suite (P1) | Not Started | — | — |
| 12 | Recruiting & Onboarding (ATS) | [Specs/06](Specs/06-recruiting.md) | Talent suite (P1) | Not Started | — | — |
| 13 | Performance Management | [Specs/07](Specs/07-performance.md) | Talent suite (P1) | Not Started | — | — |
| 14 | Learning & Development (LMS) | [Specs/08](Specs/08-learning.md) | Compliance engine P0; rest P1 | Not Started | — | — |
| 15 | Succession & Career Planning | [Specs/09](Specs/09-succession.md) | Talent suite (P1) | Not Started | — | — |
| 16 | Migration & Parallel Run | [Specs/16](Specs/16-migration.md) | Program-long | Not Started | — | — |

## Open Gates (block design in affected modules)

Tracked in detail in [Specs/00-INDEX.md](Specs/00-INDEX.md):

| Gate | Affects modules | Status |
|---|---|---|
| Payroll provider RFP | 03, 16 | Open |
| Performance ratings philosophy | 07, 05, 09 | Open |
| ATS/LMS build-vs-buy | 06, 08 | Open |
| IN/CN data-residency rulings | 15 | Open (EU plane confirmed) |
| Works-council consultation inventory | 16 | Open |

## Progress Log

Reverse-chronological. Entry format defined in `.claude/skills/update-progress/SKILL.md`.

### 2026-06-10 — Module 15 (Foundation): implemented, all tests passing — paused for user review
- **Status:** Design → In Progress → Testing (awaiting review)
- **Requirement IDs:** TECH-4 (temporal library + conformance suite), TECH-5 (policy engine, tiers T0–T3, decision log), TECH-6 (hash-chained append-only audit), TECH-7 partial (envelope-encryption stub, local KEK), TECH-9/10 (data catalog + generated records-of-processing)
- **Done:** `src/platform_core/` built (temporal, policy, audit, catalog, crypto, FastAPI app); PostgreSQL 17 installed, databases `meridian`/`meridian_test` created; Alembic migration 0001 verified up/down/up; **pytest: 25 passed, 0 failed** including named edge-case tests `test_TECH_clock_skew_effective_ordering`, `test_TECH_audit_surge_bulk_read_logging`, `test_TECH_policy_unavailable_fails_closed`. Cross-surface policy consistency proven (API vs in-process). Reusable `TemporalConformanceSuite` ready for future modules.
- **Next:** user review of Module 1; on acceptance of the 3 N/A-local deferrals (region failover, Kafka lag, KMS drill) mark Done, then start Module 2 (Specs/12 Workflow & Rules) with `design-module`.
- **Blockers:** none.

### 2026-06-10 — Module 15 (Foundation): design doc written; build phase scaffolding finalized
- **Status:** Not Started → Design
- **Requirement IDs:** TECH-3/4/5/6/7/9/10 traced in [TechDesignDoc/15-foundation-design.md](TechDesignDoc/15-foundation-design.md)
- **Done:** Stack decided (Python 3.11.9 + FastAPI backend, React/Vite UI, local PostgreSQL 17; events deferred — recorded in `.claude/memory.md`). Folders `src/`, `src/test/`, `UI/`, `TechDesignDoc/` in place. New skill `update-design-doc`; skills repointed to TechDesignDoc. PostgreSQL 17 install started via winget.
- **Next:** scaffold Python project, implement temporal library (TECH-4) slice.
- **Blockers:** none.

### 2026-06-10 — Program: build-phase scaffolding created
- **Status:** specification phase complete; no module started.
- **Done:** Specs moved to `Specs/`; CLAUDE.md and README updated; `.claude/memory.md` and skills created (`design-module`, `implement-module`, `temporal-schema`, `api-contract`, `edge-case-tests`, `update-progress`); this tracker created.
- **Next:** start Module 15 (Tech, Security & Privacy foundation) with the `design-module` skill — it underpins every other module (temporal platform service, policy service, audit).
- **Blockers:** none for Module 15; five program gates remain open (table above).

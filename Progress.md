# Project Meridian — Build Progress

Single source of truth for module-by-module build status. Updated after **every** unit of work (design doc, schema, slice, tests). See the `update-progress` skill in `.claude/skills/` for the entry format and status rules.

**Status legend:** `Not Started` → `Design` → `In Progress` → `Testing` → `Done`
A module is `Done` only when its PRD Edge Cases Register is fully covered by passing named tests.

**Execution rule:** one module at a time, in build-order below, unless the user directs otherwise.

## Module Status

Build order follows the phase anchors in [Specs/00-INDEX.md](Specs/00-INDEX.md): platform foundations first, then Core HR, then the operational core, then the talent suite. Migration (16) runs program-long alongside.

| # | Module | Spec | Phase | Status | Design Doc | Edge-Case Tests |
|---|--------|------|-------|--------|------------|-----------------|
| 1 | Tech, Security & Privacy foundation | [Specs/15](Specs/15-technical-architecture.md) | Foundation (P0) | Not Started | — | — |
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

### 2026-06-10 — Program: build-phase scaffolding created
- **Status:** specification phase complete; no module started.
- **Done:** Specs moved to `Specs/`; CLAUDE.md and README updated; `.claude/memory.md` and skills created (`design-module`, `implement-module`, `temporal-schema`, `api-contract`, `edge-case-tests`, `update-progress`); this tracker created.
- **Next:** start Module 15 (Tech, Security & Privacy foundation) with the `design-module` skill — it underpins every other module (temporal platform service, policy service, audit).
- **Blockers:** none for Module 15; five program gates remain open (table above).

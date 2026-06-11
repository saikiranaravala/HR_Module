---
name: design-module
description: Produce a technical design document for a Meridian module from its domain PRD before any code is written. Use when starting a new module or when asked to "design" a module (e.g., "design core-hr").
---

# Design a Meridian Module

Turn a domain PRD in `Specs/` into an implementable technical design. Design comes before code — a module's status in `Progress.md` moves `Not Started → Design` when this skill runs.

## Steps

1. **Read the sources in order:** the module's PRD in `Specs/NN-*.md`, its section in `Specs/PRD-Meridian-HCM.md` (canonical for requirement IDs + P0/P1/P2 priority), and `Specs/15-technical-architecture.md` for platform constraints.
2. **Check gates:** compare the module against the five cross-cutting decision dependencies in `Specs/00-INDEX.md`. If gated, the design must isolate the undecided part behind an interface and say so explicitly.
3. **Check memory:** scan `.claude/memory.md` for prior decisions affecting this module.
4. **Write the design doc** to `Design/NN-<module>-design.md` with these sections:
   - **Scope & requirement trace** — table of requirement IDs (from master PRD) → design element. Every P0 requirement must appear. Anything not covered by an ID gets flagged, not invented.
   - **Bounded context & data model** — entities, which are effective-dated (temporal pattern: `effective_date` + `effective_sequence` + action/reason + audit columns), sensitivity tier (T0–T3) per field, catalog tags (category, purpose, lawful basis, retention class).
   - **APIs & events** — REST resources (OpenAPI 3.1 style, `/v1`, cursor pagination, idempotency keys, RFC7807), domain events (CloudEvents, PII-minimized payloads).
   - **Rules & configuration surface** — what varies by country/population and therefore lives in decision tables / workflow config / country packs, never in code branches.
   - **AI touchpoints** — which use cases route through the AI Gateway, their risk tier, and the human-approval gate for anything touching money/employment/access.
   - **Edge-case test plan** — every row of the PRD's Edge Cases Register mapped to a named test (e.g., `test_CORE_multi_job_cross_entity`).
   - **Open items** — gated decisions, PRD conflicts found (surface, don't resolve silently).
5. **Verify against the eight Architecture Invariants** in `CLAUDE.md` — list each invariant and how the design honors it. If one is violated, stop and raise it.
6. **Update `Progress.md`:** set module status to `Design`, append a dated log entry citing the requirement IDs covered.

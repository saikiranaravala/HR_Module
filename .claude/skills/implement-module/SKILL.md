---
name: implement-module
description: Implement a Meridian module from its approved design doc — scaffold the service, schema, APIs, events, and tests. Use when asked to "build" or "implement" a module whose design exists in TechDesignDoc/.
---

# Implement a Meridian Module

Build a module from its design doc. Precondition: `TechDesignDoc/NN-<module>-design.md` exists and the module is in `Design` status in `Progress.md`. If the design doc is missing, run the `design-module` skill first — do not implement straight from a PRD.

## File placement (fixed)

- Backend code: `src/<context_package>/` (Python 3.11, FastAPI + SQLAlchemy 2.x) — one package per bounded context, snake_case (e.g., `src/platform_core/`, `src/core_hr/`).
- Tests: `src/test/<context_package>/` mirroring the package.
- Frontend: `UI/` (React via npm/Vite, Node 24).
- Design docs: `TechDesignDoc/` — when implementation deviates from the design, run the `update-design-doc` skill in the same slice.

## Steps

1. **Read** the design doc, the module PRD in `Specs/`, and `.claude/memory.md`. Confirm no open gate blocks the slice being built.
2. **Work in vertical slices**, one requirement ID at a time, P0s first. For each slice:
   - Schema first (use the `temporal-schema` skill for effective-dated entities). A new/changed table needs **both** the ORM model and an Alembic migration, and they must agree exactly — tests build schemas from `Base.metadata` while the dev DB comes from migrations, so drift shows up as "tests green, dev DB broken" (or vice versa).
   - Migration discipline: next revision on the single chain in `migrations/versions/`; verify **up/down/up** before calling the slice done; regenerate `SQL/DDL/` (`SQL/DDL/_generate.py`) after the migration lands.
   - API contract next (use the `api-contract` skill).
   - Service logic, with country/population variation in config or country packs — never `if country == 'XX'` in code.
   - Events: **deferred locally** (see `.claude/memory.md`) — use direct service calls across contexts for now, shaped so a CloudEvents emission can replace them when the event layer lands. When events return: schema-registered, PII-minimized, idempotent consumers.
   - Authorization: every read/write path calls the central policy service; T2/T3 reads are audit-logged. No local access logic.
   - Tests in the same slice, not deferred (see Testing Requirements in `CLAUDE.md`).
   - Ordering that must survive concurrency: never order rows by wall-clock timestamps alone (Windows timer resolution makes same-timestamp rows non-deterministic) — use a DB `Identity`/sequence column (see `succession.ninebox_placement.seq`, migration 0017).
3. **AI features:** all model calls go through the AI Gateway; agents inherit the calling user's scope; human-approval gates on money/employment/access mutations. Prompts go in the prompt registry, not inline.
4. **Before declaring a slice done:** run the tests and show the output. A failing or skipped test means the slice is not done — say so plainly.
5. **Module exit criteria:** all P0 requirement IDs implemented; the PRD's Edge Cases Register fully covered by passing named tests; temporal conformance suite green for every effective-dated entity; policy consistency suite green.
6. **Update `Progress.md`** after every slice: dated log entry with requirement IDs, what was built, test results. Move status `In Progress → Testing → Done` as criteria are met.
7. **Record learnings:** anything non-obvious discovered during implementation (a PRD ambiguity, a pattern that worked, a constraint hit) goes in `.claude/memory.md`.

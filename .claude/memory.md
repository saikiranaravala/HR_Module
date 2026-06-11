# Project Meridian — Memory

Durable decisions, learnings, and context that future sessions need. Append-only: add dated entries; never silently rewrite history. If a decision is reversed, add a new entry that supersedes the old one and links back to it.

Format for entries:

```
## YYYY-MM-DD — <short title>
**Type:** decision | learning | constraint | convention
**What:** one or two sentences.
**Why:** the rationale (this is the part future sessions can't reconstruct).
**Affects:** modules / files / requirement IDs.
```

---

## 2026-06-10 — Hash-chain payloads must canonicalize timestamps to UTC
**Type:** learning
**What:** Postgres `timestamptz` values come back in the session timezone, so any hash computed over `isoformat()` at write time breaks on re-verification unless the payload converts to UTC first (`astimezone(timezone.utc)`). Fixed in `platform_core/audit.py::_hash_payload`.
**Why:** Cost 3 test failures on first run; will bite any future content-hashing over timestamptz columns (payslip snapshots, reconciliation evidence).
**Affects:** platform_core.audit, future Modules 03/16 snapshot hashing.

## 2026-06-10 — Default PostgreSQL local credentials
**Type:** convention
**What:** Local PostgreSQL 17 (winget, service `postgresql-x64-17`): superuser `postgres`/`postgres`; app role `meridian_dev`/`meridian_dev` owning databases `meridian` (dev, alembic-managed) and `meridian_test` (tests, schema recreated per run). URLs in `src/.env` (git-ignored).
**Why:** Dev-only credentials; every session needs them for psql/alembic work.
**Affects:** src/.env, alembic, all test runs.

## 2026-06-10 — Stack decision: Python backend + React UI + local PostgreSQL
**Type:** decision
**What:** Backend services in Python 3.11.9 (FastAPI, SQLAlchemy 2.x, Alembic, pytest); UI in React via npm/Vite (Node v24.14.0, npm 11.11.0); database is a local PostgreSQL instance (database `meridian`). Toolchain versions are pinned to what's on the user's machine.
**Why:** User choice via stack questions on 2026-06-10. Mixed stack: Python for domain logic, Node only for the UI build chain.
**Affects:** all of src/, UI/, every design doc's tech sections.

## 2026-06-10 — Events deferred (deliberate Invariant #7 deviation)
**Type:** constraint
**What:** No Kafka/event backbone locally; services use direct calls for now. CloudEvents contracts, outbox, and idempotent consumers are NOT being built yet. Re-enabled when a dedicated event-layer module is built (target: alongside Module 13 Integration, user to confirm).
**Why:** User chose "skip events for now" to move faster; recorded so the deviation is visible, not silent. Domain code should still avoid baking in synchronous coupling that an event layer can't later replace.
**Affects:** Architecture Invariant #7, Specs/13, every module's events section.

## 2026-06-10 — Folder layout fixed for build phase
**Type:** convention
**What:** `TechDesignDoc/` = design docs (one per module, with change log); `src/<context_package>/` = backend; `src/test/<package>/` = tests; `UI/` = React app. Skills `update-design-doc` keeps docs in sync with code.
**Why:** User directive 2026-06-10.
**Affects:** all build artifacts.

## 2026-06-10 — Repository restructured for build phase
**Type:** convention
**What:** All 17 spec documents moved from repo root into `Specs/`. `Progress.md` (root) tracks module-by-module build status; `.claude/skills/` holds reusable workflows; this file holds durable memory.
**Why:** Separates immutable specification from living build artifacts as implementation begins.
**Affects:** all paths in CLAUDE.md, README.md.

## 2026-06-10 — Module-by-module execution model adopted
**Type:** decision
**What:** The product is built one module at a time, in the phase order defined in `Specs/00-INDEX.md` (Foundation P0 → Operational core P0 → Talent suite P1). Every unit of work updates `Progress.md`.
**Why:** User directive; keeps scope controlled and progress auditable.
**Affects:** Progress.md, all modules.

## 2026-06-10 — Five gating decisions remain open
**Type:** constraint
**What:** Payroll provider RFP, performance ratings philosophy, ATS/LMS build-vs-buy, IN/CN data-residency rulings, works-council inventory are all undecided (see `Specs/00-INDEX.md`).
**Why:** Designs in gated areas (03, 05, 06, 07, 08, 09, 15, 16) must flag the dependency and avoid hard-committing to one outcome.
**Affects:** Specs/03, 05–09, 15, 16.

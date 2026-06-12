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

## 2026-06-11 — Shared helpers: org-path boundaries and calendar months
**Type:** convention
**What:** `platform_core.orgpath.within/normalize` is the only sanctioned way to test org-subtree membership (raw `startswith` lets '/corp/eng' match '/corp/engineering'); `platform_core.dates.add_months` is the only sanctioned month arithmetic for statutory/retention windows (months*30 drifted ~10 days on a biennial compliance anniversary). Both born from the 2026-06-11 program review.
**Why:** Three modules had independently hand-rolled each pattern; two had latent boundary/drift bugs.
**Affects:** ess_mss, analytics, succession, learning, recruiting; every future module touching org paths or month windows. Note: `policy/engine._scope_matches` still uses raw startswith (pre-existing, role subtrees end with '/') — migrate when policy config is next touched.

## 2026-06-11 — Program review: deferred findings (not fixed, recorded)
**Type:** learning
**What:** Full-program review (post Module 16) deferred these: (1) `compensation.cycles.committed_spend` is O(n²) at 50K-line cycles — maintain a running total per cycle when the cloud phase tunes for the <20-min recalc acceptance; (2) `analytics.reports.run_report` does a per-row policy decide — batch by (country, org_path) group; (3) SUPPRESSION_THRESHOLD=5 duplicated in ess_mss/team.py and analytics/suppression.py (move to platform_core when next touched); (4) ORM `Base.metadata.create_all` (tests) vs Alembic migrations can drift on nullability/server defaults (e.g. JSONB columns without `Mapped[]` are nullable in metadata, NOT NULL in migrations) — a metadata-vs-migration diff check would catch it; (5) `case-routing` ruleset v1 effective 2026-06-01: backdated `opened_at` before that raises NoRuleVersionError.
**Why:** Real but non-blocking at local scale; recording so they aren't rediscovered.
**Affects:** compensation, analytics, ess_mss, all model/migration pairs.

## 2026-06-11 — UI conventions (v1 shell)
**Type:** convention
**What:** `UI/` is React 19 + TS + Vite, react-router-dom only; the design system is owned CSS (`UI/src/styles.css` tokens: navy #15324E, teal #0E8074, amber #F2A33C) reproducing PeopleSoft grammar (tiles, breadcrumb bar, psgrid). `UI/src/data.ts` is the demo data layer whose shapes mirror the Python models 1:1 — the REST client replaces it without page changes; store actions in `UI/src/store.tsx` are dispatch-shaped for that swap. Personas (employee/manager/hr) drive nav + homepage tiles.
**Why:** User directive: best-in-class UI, PS look-and-feel with own branding, minimum clicks. No component library keeps the brand owned and the bundle small (93KB gz).
**Affects:** UI/, future REST/i18n work, TechDesignDoc/17.


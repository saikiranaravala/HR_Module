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

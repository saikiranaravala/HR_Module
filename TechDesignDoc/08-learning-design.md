# Module 14 Design — Learning & Development (Specs/08)

**Spec:** [Specs/08-learning.md](../Specs/08-learning.md) · **Package:** `src/learning/` · Tests: `src/test/learning/`
**Depends on:** platform_core (audit), rules_workflow (config patterns), core_hr (population attributes), feeds 09-Succession / 02-TIME gating checks
**⚠ Gate:** LMS build-vs-buy OPEN (master §13.7; PRD assumes build). Isolation: the **compliance engine** (the differentiator, P0) plus completion-evidence records are canonical and survive a "buy" outcome — a partnered delivery platform would push completions into these same records via the adapter layer.

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| LEARN-2 (**P0**) | `compliance.py`: requirement objects from **jurisdiction packs** (`config/jurisdiction_packs.yaml` — CA SB1343 biennial 2h/1h, NY/IL annual, OSHA role-based), population rules (role/location/worker-type), initial deadline + rolling-anniversary or fixed-date recurrence, grace, escalation ladder (T-14 worker → T-7 manager → overdue HR/compliance), policy-gated consequence hooks (safety assignment-block flag) | **Yes** (dashboards = UI phase; <1 h re-eval = direct call locally) |
| LEARN-1 (P1) | `catalog.py`: content items with **version supersede policy** (in-progress finish-old vs restart), completion records **pinning content version** (audit answer for "which version in 2027"), equivalency mapping (evidence + approver); `scorm.py`: suspend/resume with corruption fallback | **Yes** (ILT sessions/waitlists, external-provider catalog sync = adapter slice) |
| LEARN-3 (P1) | `certs.py`: certification registry, 90/60/30 expiry pipeline, job-requirement linkage → compliance flag (+ optional policy-gated assignment block) | **Yes** |
| LEARN-4 (P2) | Tuition reimbursement | Deferred |
| LEARN-5 (P2) | AI skills inference / recommendations | Deferred (would enter via 14-AI registry) |

## 2. Data Model (schema `learning`)

| Table | Notes | Tier |
|---|---|---|
| `content_item` | version chain, `supersede_policy` finish-old\|restart | T0 |
| `assignment` | requirement key, due date, status, `paused_until`/pause lineage, extension + evidence note, attempts, suspend data + checksum | T1 |
| `completion_record` | **immutability-guarded** audit evidence: worker, content version pinned, score, completed_at, source (native\|import\|equivalency) | T1 |
| `certification` | issuer, validity, expiry, evidence ref, job-required flag | T1 |

Catalog tags: category `learning`, purpose `learning-compliance`, lawful basis `legal-obligation` (compliance) / `legitimate-interest` (development), retention `learning-audit-7y`.

## 3. Rules & Configuration Surface

- `config/jurisdiction_packs.yaml` — versioned regulation packs with regulatory-change notes (shared model with Core country packs; new pack = config deploy, the <5-day acceptance).
- Requirement `applies_to` lists worker types — **contractor scope** (register row) is a pack attribute, not a code branch.
- Escalation ladder offsets are pack-level config.

## 4. AI Touchpoints

None locally (LEARN-5 deferred). Future skills inference is worker-confirmable ("self-sovereign profile") and enters via the 14-AI governance registry.

## 5. Edge-Case Test Plan (register §8)

| Register row | Test |
|---|---|
| Leave during compliance window (clock pause) | `test_LEARN_leave_pauses_compliance_clock` |
| Vendor outage in deadline week (batch extension + evidence note) | `test_LEARN_vendor_outage_batch_extension` |
| SCORM suspend-data corruption (resume fallback, attempt protected) | `test_LEARN_scorm_suspend_corruption_fallback` |
| Acquired-population transcript import (compliance-relevant minimum) | `test_LEARN_acquired_transcript_import` |
| Contractor training scope (lightweight records) | `test_LEARN_contractor_lightweight_scope` |

## 6. Key Decisions / Invariant Notes

- **Completion records are immutable** (DB guard) — they are the audit evidence; corrections are new records, the lineage explains itself.
- Version pinning at completion time, supersede policy at content level: in-progress learners on `finish-old` keep their version; `restart` voids in-progress assignments back to `assigned`.
- Clock pause = explicit pause window appended to the assignment (due date shifts by paused days when resumed) — never a silent due-date edit; extension batches carry a mandatory evidence note (regulator-facing).
- Consequence hooks (assignment-block for safety roles) emit a **flag for the policy layer**; Learning never blocks access itself (Invariant #3).

## 7. Open Items

- LMS build-vs-buy gate (above); LRS retention policy (spec §9). ILT/external-provider adapters land with 13-Integration slices.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 08 kickoff (auto-approved cadence).
- **2026-06-11** — Review fix: rolling-anniversary recurrence uses calendar months (`platform_core.dates.add_months`) instead of months*30 (a biennial anniversary drifted ~10 days).

# Module 6 Design — Time & Labor + Absence (Specs/02)

**Spec:** [Specs/02-time-labor.md](../Specs/02-time-labor.md) · **Package:** `src/time_labor/` · Tests: `src/test/time_labor/`
**Depends on:** rules_workflow (OT thresholds, minor caps as decision tables), core_hr (multi-job, is_minor), platform_core

## 1. Scope & Requirement Trace

| Spec section | Design element | Local scope |
|---|---|---|
| §2 Time capture | `TimeEntry` — UTC instants + IANA tz stored together (register: DST); elapsed computed from UTC, attribution by LOCAL shift-start date (register: midnight-spanning) | **Yes** (web-grid/geofence/clock adapters deferred) |
| §3 Rules (the heart) | OT thresholds as ruleset `overtime-thresholds` (US FLSA weekly-40; US-CA daily 8/12 doubletime; defaults) — versioned, effective-dated config; calc orchestration in `services.calculate_period` with per-line explanations (§3 explainability) | **Yes** (CBA variants/premiums/rounding deferred; default no-rounding = litigation-safe) |
| §4 Accruals | `AccrualLot` — grant, caps, carryover lots with expiry, FIFO consumption, negative-balance limit, future-balance projection | **Yes** (statutory catalogs as config later) |
| §6 Period close | `lock_period` → compile to canonical elements (earnings code × hours × rate context) → immutable `TimeResult` snapshot; post-lock retro engine with the reconciliation identity (original + delta = recalculated) | **Yes** |
| §5 Scheduling | Deferred (P1) | No |

## 2. Edge-Case Test Plan (register §8)

| Register row | Test |
|---|---|
| Midnight-spanning shifts | `test_TIME_midnight_spanning_shift_attribution` |
| DST transitions (23/25-hr days) | `test_TIME_dst_transition_hours_from_utc` |
| Transfer mid-period across pay groups | `test_TIME_mid_period_transfer_split_results` |
| Retro pay-rate change on locked period | `test_TIME_retro_rate_change_delta_reconciles` (the §6 acceptance identity) |
| Multi-job combined-hours OT (FLSA) | `test_TIME_multi_job_combined_hours_ot` |
| Minors' hour caps | `test_TIME_minor_hour_cap_violation_detected` |
| Leave during notice period | Deferred (needs Module 02 absence-flow + Core HR notice tracking slice) |

## 3. Key decisions

- **CA daily/weekly interplay simplified**: daily OT extracted first, weekly-40 applied to remaining straight time. Documented simplification; full CA 7th-day rules arrive with the country-pack slice.
- **TimeResult is an immutable snapshot per (worker, period, lock)** — retro never edits it; deltas are new rows with `is_retro_delta` lineage to the original compile.
- Every result line carries `explanation` (rule version + source hours) — the "explain this 1.5× line" view.

## Change Log

- **2026-06-10** — Initial design + implementation. Trigger: Module 6 kickoff (auto-approved cadence).

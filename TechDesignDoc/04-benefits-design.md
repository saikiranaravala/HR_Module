# Module 8 Design — Benefits Administration (Specs/04)

**Spec:** [Specs/04-benefits.md](../Specs/04-benefits.md) · **Package:** `src/benefits/` · Tests: `src/test/benefits/`
**Depends on:** rules_workflow (eligibility rules), payroll_hub (CPDC deduction elements), platform_core

## 1. Scope & Requirement Trace

| Spec section | Design element | Local scope |
|---|---|---|
| §2 Plan model | `BenefitPlan` + `BenefitRate` (effective-dated rate rows: age band, tier, salary multiple for life; employer/employee split) | **Yes** (plan-year clone tooling deferred) |
| §3 Eligibility | ruleset `benefits-eligibility` (worker type, FTE, country) + waiting-period date math (`first_of_month_after`) | **Yes** (ACA look-back deferred — needs TIME variable-hour history) |
| §4 Enrollment | new-hire window with default-on-expiry; life-event catalog with allowed-change matrix (Section 125 consistency); EOI pending state | **Yes** (OE waves/UX deferred) |
| §6 Payroll interlock | deduction derivation: annual rate → per-period (24/26), GTL imputed income (Table I simplified) → CPDC elements | **Yes** |
| §5 Carrier EDI-834, §7 ACA forms | Deferred (adapter exists in chassis; 834 mapping later) | No |

## 2. Edge-Case Test Plan (register §9)

| Row | Test |
|---|---|
| Dual-covered couples (dependent conflict) | `test_BEN_dual_covered_dependent_conflict` |
| Retro divorce reported late (clawback window) | `test_BEN_retro_divorce_clawback_window` |
| Mid-OE termination | `test_BEN_mid_oe_termination_cancels_pending` |
| EOI denied after default coverage started | `test_BEN_eoi_denied_reverts_to_default` |
| Rehire within ACA stability / LOA premium / acquisition mid-year | Deferred (ACA look-back, leave phases, M&A slices) |

## Change Log

- **2026-06-11** — Initial design + implementation. Trigger: Module 8 kickoff (auto-approved cadence).
- **2026-06-11** — Waiting-period semantics pinned: `first_of_month_after(start, days)` returns the first of the month **strictly after** `start + days` — a threshold landing exactly on the 1st rolls to the next month ("following", not "coinciding with"), anchored on **hire date** (not election date). Spec §3 only says "first-of-month-after-30-days style"; this is the plan-document-standard reading. Fixed the day==1 branch in `benefits/services.py` and one test expectation. Migration `0008_benefits` added (up/down verified); suite 11/11.

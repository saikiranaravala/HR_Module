# Module 11 Design — Compensation Planning & Administration (Specs/05)

**Spec:** [Specs/05-compensation.md](../Specs/05-compensation.md) · **Package:** `src/compensation/` · Tests: `src/test/compensation/`
**Depends on:** platform_core (temporal pattern — comp is Invariant-#1 territory; policy T2), rules_workflow (approval matrix), payroll_hub (CPDC elements), core_hr (assignments)
**⚠ Gate:** performance-ratings philosophy (Specs/00-INDEX) is OPEN — the guideline matrix takes the rating as an opaque config key (`config/guidelines.yaml`); a ratingless philosophy becomes a single-row matrix. No code change needed when the decision lands.

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| COMP-1 (P0) | `GradeRange` (temporal: grade×country ranges min/mid/max), geo differentials (`config/geo_zones.yaml`), pay-components catalog with taxability/pensionability metadata (`config/components.yaml`), `CompRecord` (temporal, T2) with **server-side compa-ratio / range-penetration**; comp-change transaction: reason taxonomy, guideline display, out-of-range / >cap% ⇒ comp-team approval flag | **Yes** |
| COMP-2 (P1) | `cycles.py`: cycle with **population snapshot frozen at open** (mid-cycle org moves = explicit snapshot policy), budget pool with live enforcement, guideline matrix (rating × compa-quartile, config), out-of-guideline mandatory justification, **FX locked at cycle open** with variance reporting, manager worksheet recommendation flow | **Yes** (n-level roll-up/calibration UX, statementing = UI phase) |
| COMP-3 (P1) | Equity administration | **Deferred** — equity platform of record undecided (spec §9 open question); grant/vesting model lands with the adapter |
| COMP-4 (P2) | Pay-equity workbench, survey import | **Deferred** (P2; privilege-mode requirements noted) |
| COMP-5 (P1) | Total rewards statement | **Deferred** to ESS statement slice (data sources: comp + benefits already built) |

## 2. Data Model (schema `comp`)

| Table | Notes | Tier |
|---|---|---|
| `grade_range` | TemporalMixin; identity `range_key` ("G7:US"); currency, min/mid/max | T1 |
| `comp_record` | TemporalMixin; identity `comp_key` (uuid5 of worker+role); worker_id, `record_role` home\|host-shadow (dual-currency expats), base_annual, currency, grade, country, fte | **T2** (read-logged) |
| `comp_cycle` | status, corporate currency, **fx_rates JSONB locked at open**, budget_pool, snapshot_at | T1 |
| `cycle_line` | frozen worksheet row (snapshot JSONB: salary, rating, compa-ratio at open), merit_pct, justification, out_of_guideline, status (incl. `routed-skip-level`) | T2 |

Catalog tags: category `compensation`, purpose `comp-administration`, lawful basis `contract`, retention `comp-7y`. CompRecord runs the **TemporalConformanceSuite** (as-of, sequence, retro, audit, DB immutability).

## 3. Rules & Configuration Surface

- `config/guidelines.yaml` — merit matrix: rating × compa-quartile → recommended % range + hard cap. Rating keys are opaque strings (gate isolation).
- `config/geo_zones.yaml` — metro-zone differentials (zone → % of national).
- `config/components.yaml` — pay-component catalog: taxability/pensionability per country handled as component metadata, never code branches.
- Approval matrix constants: out-of-range or >12% ⇒ comp-team approval (decision-table candidate when thresholds vary by country).

## 4. AI Touchpoints

None. (Spec §6: comp is the most-audited domain; no AI draft surface until a registered use case exists. AI never recommends ratings — Invariant #6 — and the guideline matrix is deterministic config.)

## 5. Edge-Case Test Plan (register §8)

| Register row | Test |
|---|---|
| Promotion + merit in same cycle (sequencing & range basis) | `test_COMP_promo_plus_merit_sequencing` |
| Retro merit after termination (final-pay supplement) | `test_COMP_retro_merit_after_termination_supplement` |
| FX swing mid-cycle (locked rate, variance reported) | `test_COMP_fx_locked_variance_reported` |
| Below new range min post-refresh (remediation proposal) | `test_COMP_range_refresh_remediation_list` |
| Manager self-recommendation block (skip-level routing) | `test_COMP_manager_self_recommendation_skip_level` |
| Dual-currency expats (home/host shadow split) | `test_COMP_dual_currency_expat_shadow` |

## 6. Key Decisions / Invariant Notes

- **Promo+merit sequencing pinned:** merit % applies to the pre-promotion salary, the promotion increase follows, and range validation runs against the **new** grade's range. One documented order, not per-team behavior.
- **Comp records are temporal** via `insert_temporal` only — retro merit writes a retro row + audit (Invariant #1); after termination it additionally emits a final-pay supplement element for payroll (no silent base-pay edit on a terminated record).
- Cycle FX is locked in the cycle row at open; later market rates only ever produce a **variance report**, never a recalc of committed lines.
- T2 sensitivity on all comp values; reads of comp data go through policy + read-audit (most-audited domain, spec §6).

## 7. Open Items

- Ratings philosophy gate (above). Equity platform of record (COMP-3 deferred). Bonus accrual feed to Finance (spec §9, recommend P1.5).

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 05 kickoff (auto-approved cadence).

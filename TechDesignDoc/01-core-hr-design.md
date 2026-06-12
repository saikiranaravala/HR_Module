# Module 5 Design — Core HR & Workforce Administration (Specs/01)

**Spec:** [Specs/01-core-hr.md](../Specs/01-core-hr.md) · **Package:** `src/core_hr/` · Tests: `src/test/core_hr/`
**Depends on:** platform_core (temporal, policy, audit, crypto, catalog), rules_workflow (country patterns), integration_hub (JML on termination)

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| CORE person model (§2.1) | `Person` (stable) + `PersonName` (temporal, effective-dated legal names) + `NationalId` (envelope-encrypted value, masked display, reveal-audited) + `WorkEligibility` (permit expiry blocking rule) | **Yes** (Address/Contact/Dependent/Bank deferred to ESS slice) |
| CORE-3 multi-job (§2.2) | `Worker` = person × legal entity (stable identity, N concurrent per person); `Assignment` = the temporal series per worker (EFFDT/EFFSEQ, action/reason, status) — the PeopleSoft JOB pattern done right | **Yes** |
| Position/Department (§2.3–2.4) | `Department` (tree) + `Position` with vacancy logic (headcount − incumbents); org effective-dating deferred (operational tables + audit for now) | Partial |
| Hire/rehire (§3.1) | `services.hire()` — duplicate check (national-ID exact, name+DOB fuzzy) → rehire path bridges `original_hire_date` | **Yes** |
| Transfer (§3.2) | `services.transfer()` — country pattern from ruleset `transfer-pattern` (DE cross-entity = terminate+rehire; US = continuous); one logical operation either way | **Yes** |
| Termination (§3.4) | `services.terminate()` — TER assignment row + JML disable action (≤15 min SLA path via integration_hub) | **Yes** |
| Leave eligibility (§3.3) | FMLA 1,250-hour/12-month test as ruleset `fmla-eligibility` | **Yes** (entitlement timelines deferred to Module 02) |
| §4 compliance packs, §3.5 reorg studio | Deferred (content + mass-ops slices) | No |

## 2. Edge-Case Test Plan (register §6 → named tests)

| Register row | Test |
|---|---|
| Retro hire-date correction after first payroll | `test_CORE_retro_hire_date_correction_after_payroll` |
| Concurrent multi-country jobs | `test_CORE_concurrent_multi_country_jobs` |
| Rehire bridging (incl. prior-balance flag) | `test_CORE_rehire_bridges_original_hire_date` |
| Future-dated promotion overlapping pending transfer | `test_CORE_overlapping_changes_resolve_by_sequence` |
| Department inactivation with active incumbents | `test_CORE_department_inactivation_blocked` |
| Assignment past work-permit expiry (blocking rule §2.1) | `test_CORE_assignment_blocked_past_permit_expiry` |
| Name change mid payroll cycle | Partial: effective-dated name change + audit implemented; payroll-cycle lock arrives with Module 03 |
| Minor employees hour restrictions | Partial: `is_minor` exposed for Module 02 rules; permit rules covered above |

## 3. Invariant check

1 Temporal ✔ (PersonName + Assignment via TemporalMixin + conformance suite) · 2 Schema `core` ✔ · 3 Policy ✔ (reads through serialize/read_with_audit patterns; national-ID reveal = T2 read audit) · 6 n/a here · 8 ✔ all columns tagged.

## Change Log

- **2026-06-10** — Initial design + implementation. Trigger: Module 5 kickoff (auto-approved cadence).

# Module 7 Design — Payroll Integration Hub (Specs/03)

**Spec:** [Specs/03-payroll-hub.md](../Specs/03-payroll-hub.md) · **Package:** `src/payroll_hub/` · Tests: `src/test/payroll_hub/`
**Depends on:** integration_hub (adapter chassis), time_labor (TimeResults), platform_core
**Gate note:** provider portfolio RFP is OPEN — everything provider-specific sits behind the adapter interface (`MockProviderAdapter` locally); PAY-9 portability is the design constraint.

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| §2 CPDC | `cpdc.py` — canonical pay record (dataclass), element dictionary YAML with per-country activation; **no provider code upstream of adapters** (Invariant #4) | **Yes** |
| §4 Cycle state machine | `cycle.py` + `PayCycle` — Draft → Inputs-Compiled (immutable snapshot + hash) → Validated → Approved (4-eyes) → Transmitted → Results-Received → Reconciled → Closed; off-cycle same machine | **Yes** (GL-Posted/Payslips states stubbed) |
| §5 PAY-3 gate | 3 layers: structural (mandatory-by-country), business (retro sanity %), anomaly heuristics (trailing-cycle variance, bank-change-near-payday). Severity BLOCK / HOLD-RECORD (excluded + retro auto-queued) / WARN. **Nothing transmits with blocking errors.** | **Yes** (AI scoring = heuristic locally; gateway hookup later) |
| §3 Adapter | `MockProviderAdapter(Connector)` — CPDC→provider mapping inside the adapter; mini conformance kit (golden scenarios) | **Yes** |
| §6 Results | net = gross − deductions identity; headcount match (added/dropped record = critical alert) | **Yes** (payslip render/GL engine deferred) |
| §7 Reconciliation | element-level three-way compare + variance classification (timing/mapping/rounding/population/defect) | **Yes** (workbench UI deferred) |

## 2. Edge-Case Test Plan (register §10 + CLAUDE.md payroll-path requirements)

| Row | Test |
|---|---|
| Negative net (arrears policy) | `test_PAY_negative_net_arrears_policy` |
| Mid-cycle legal-entity transfer | `test_PAY_mid_cycle_entity_transfer_split` |
| Deceased-worker final pay | `test_PAY_deceased_worker_beneficiary_payee` |
| Multi-state allocation | `test_PAY_multi_state_allocation_must_sum_100` |
| Provider outage at cut-off | `test_PAY_provider_outage_pay_as_last_cycle` |
| Snapshot immutability (CLAUDE.md) | `test_PAY_snapshot_immutable_after_compile` |
| Reconciliation identity (CLAUDE.md) | covered in Module 02 retro test + `test_PAY_results_identity_net_gross` |
| FX/redenomination | Deferred (needs FX service) |

## Change Log

- **2026-06-10** — Initial design + implementation. Trigger: Module 7 kickoff (auto-approved cadence).

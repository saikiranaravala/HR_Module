# Module 2 Design — Workflow, Rules & Extensibility (Specs/12)

**Spec:** [Specs/12-platform.md](../Specs/12-platform.md) · **Package:** `src/rules_workflow/` · Tests: `src/test/rules_workflow/`
**Depends on:** platform_core (audit, catalog, policy patterns)

## 1. Scope & Requirement Trace

| Spec section | Design element | In local scope? |
|---|---|---|
| §3 Business Rules Engine | `rules.py` — decision tables in versioned, effective-dated YAML; sandboxed evaluation (no I/O, total functions); overlap/gap detection at load; golden-dataset runner | **Yes** (core) |
| §2 Workflow Engine | `workflow.py` — constrained step model (approval/notification/condition), durable DB state, routing resolvers (n-levels-up, fallback role), self-approval prevention, delegation with cycle detection, finish-on-old versioning, explain-routing audit | **Yes** (core) |
| §4 Config Lifecycle | Config = YAML artifacts in `config/rulesets/` + `config/workflows/`; every load is validated; change audit via platform audit pipeline | Partial (env promotion/freeze windows deferred) |
| §5 Document Gen / §6 Notifications | Deferred to a later slice (notification framework needs the event layer) | No |
| §7 Custom fields/objects | Deferred (P2) | No |

## 2. Rules Engine (the anti-PeopleCode core)

- **RuleSet** = YAML with `versions[]`, each `{version, effective_date, inputs, output, default, rules[]}`.
- **Version selection by transaction effective date** (edge-case register): evaluating with `transaction_date` picks the latest version whose `effective_date <= transaction_date` — rules are themselves temporal.
- Conditions: equality, enum `in`, numeric ranges (`gt/gte/lt/lte`). No expressions with side effects — evaluation is a pure function.
- **Save-time validation:** overlap detection (two rules matching the same input space) and numeric gap detection (declared min/max domain not fully covered when no default) reject the ruleset at load.
- **Golden datasets:** `run_golden(ruleset, cases)` — list of {inputs, transaction_date, expected}; 100% pass required (CI gate pattern).

## 3. Workflow Engine

- Definitions in YAML (steps: `approval | notification | condition`); no code nodes — service-call catalog deferred.
- Durable state in schema `workflow`: `workflow_instance` (definition key+version pinned at start, status, payload) and `step_execution` (resolved approver + human-readable `resolution_reason` = the explain-routing view).
- Routing resolvers: `levels-up:N` (supervisory chain via injected OrgResolver), `role:<role>`; `on_exhausted: fallback-role:<role>` handles top-of-tree (register row).
- **Engine-level guarantees:** initiator ≠ approver (self-approval blocked even if routing resolves to initiator → escalates one level); delegation resolution at evaluation time with circular-delegation detection (register row); in-flight instances finish on their pinned version (register row).
- Every transition → audit event (platform pipeline).

## 4. Edge-Case Test Plan (register → named tests)

| Register row | Test |
|---|---|
| Approver chain exhaustion → fallback role | `test_PLAT_approver_chain_exhaustion_fallback` |
| Circular delegation | `test_PLAT_circular_delegation_detected` |
| Workflow version migration, steps completed | `test_PLAT_inflight_instance_finishes_on_old_version` |
| Rule effective-dating vs transaction effective-dating | `test_PLAT_rule_version_selected_by_txn_effective_date` |
| Decision-table overlap/gap at save | `test_PLAT_decision_table_overlap_detected`, `test_PLAT_decision_table_gap_detected` |

## 5. Invariant Check

5 Config-only ✔ (this module *is* the mechanism) · 1 Temporal ✔ (rule versions effective-dated; workflow runtime state is operational, not history-bearing — instance transitions audited instead) · 3 One policy point ✔ (role resolution defers to roles; approval authority is routing, not authorization) · 7 Events — deferred (notifications need it) · 8 Privacy ✔ (all columns tagged).

## Change Log

- **2026-06-10** — Initial design. Trigger: Module 2 kickoff (auto-approved cadence).
- **2026-06-11** — `pending_for_assignee` added for the ESS/MSS inbox (Module 10), including role-queue matching (`roles=`) so fallback-routed `role:X` steps reach role members' inboxes.

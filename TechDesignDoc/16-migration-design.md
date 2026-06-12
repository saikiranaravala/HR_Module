# Module 16 Design — Migration & Parallel-Run Program (Specs/16)

**Spec:** [Specs/16-migration.md](../Specs/16-migration.md) · **Package:** `src/migration/` · Tests: `src/test/migration/`
**Depends on:** platform_core (temporal pattern, audit, immutability), payroll_hub (three-way reconciliation), core_hr (target shapes), learning (transcript import already built in 08)
**⚠ Gates:** payroll provider RFP + works-council inventory gate the **wave map**, not the factory. Everything here (pipeline, reconciliation, sync engine, gates) is wave-agnostic machinery.

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| MIG-1 (P0) | `extraction.py`: PS-shaped adapter (**PS codes never leave this module** — Invariant #4): PS_JOB EFFDT/EFFSEQ full-history mapping to canonical temporal rows, action/reason taxonomy mapping (`config/action_mapping.yaml`), rehire-bridging recompute with diff report | **Yes** (live PS connection N/A-local; adapter consumes extract rows) |
| MIG-2 (P0) | `pipeline.py`: versioned field-level mapping specs (config), **idempotent re-runs** (batch+record keyed), DQ scorecard (completeness/validity/referential/uniqueness) with threshold gates, steward exception queue with **fix-at-source guidance** | **Yes** |
| MIG-3 (P0) | `recon.py`: count + field-match per domain, **99.95% critical-field gate**, accrual recompute-and-compare with **rule-vs-data triage**, payroll variance taxonomy (incl. `env-difference` for provider test-env fidelity), **immutable signed gate artifacts** | **Yes** |
| MIG-4 (P0) | `sync.py`: bidirectional sync core — **field-ownership matrix per phase** (config), conflict detection queue (4-hour SLA), sync-lag alert >15 min, **kill-switch to one-way** | **Yes** (CDC tooling = month-1 spike, N/A-local) |
| MIG-5 (P1) | `cutover.py`: evidence-linked role-signed go/no-go checklist, **72-hour rollback decision window**, rollback retention until wave+2 clean cycles | **Yes** (comms engine/training paths ride 10/08; dashboards = UI) |

## 2. Data Model (schema `migration`)

| Table | Notes | Tier |
|---|---|---|
| `staged_record` | canonical rows out of transform, keyed (batch, source_key) for idempotency | T1 |
| `dq_exception` | steward queue: domain, rule, source ref, fix-at-source guidance, status | T1 |
| `gate_artifact` | **immutability-guarded** signed wave gate reports (entry/exit) — the program's audit trail | T1 |
| `sync_conflict` | field, both values, detected_at, SLA due, resolution | T1 |

Catalog tags: category `migration`, purpose `migration-program`, lawful basis `legitimate-interest`, retention `program-life+7y`. Staged person data inherits source tiers downstream; no PII lands in DQ/exception payloads (refs only).

## 3. Rules & Configuration Surface

- `config/mapping_specs.yaml` — versioned field-level source→target specs (owner, transform, critical flag). Mapping change control = config review.
- `config/action_mapping.yaml` — PS action/reason → Meridian taxonomy.
- `config/ownership_matrix.yaml` — per-phase field ownership for MIG-4 (phase A: PS wins everything; phase B: split by field).

## 4. AI Touchpoints

None. The factory is deterministic by design — reconciliation evidence must be explainable to auditors and works councils without model involvement.

## 5. Edge-Case Test Plan (§7 Program Risks as the register)

| Risk / register row | Test |
|---|---|
| Bidirectional sync conflicts (highest technical risk) | `test_MIG_sync_conflict_queue_and_kill_switch`, `test_MIG_sync_lag_alert` |
| Orphan integrations discovered late | `test_MIG_orphan_feed_discovery` |
| Provider test-environment fidelity gaps | `test_MIG_variance_taxonomy_env_difference` |
| Effective-dated history corrupting downstream calc | `test_MIG_recompute_triage_rule_vs_data`, `test_MIG_full_effdt_history_preserved` |
| Dual-run fatigue → gates must hold | `test_MIG_field_match_gate_9995`, `test_MIG_gate_artifact_immutable` |
| Rollback rehearsed, window enforced | `test_MIG_rollback_decision_window` |

## 6. Key Decisions / Invariant Notes

- **PS formats live only in `extraction.py`** (Invariant #4): everything downstream of the adapter speaks canonical temporal rows.
- Migrated history is loaded through `insert_temporal` shapes (EFFDT/EFFSEQ + retro semantics preserved) — never "current state only" (Invariant #1); CLAUDE.md's no-history-mutation rule holds: corrections re-run the pipeline, they never edit loaded rows.
- Idempotency = (batch_id, source_key) natural key: a re-run upserts nothing twice; the pipeline is restartable mid-batch.
- Gate artifacts are DB-immutable + content-hashed (UTC-canonicalized timestamps per memory.md learning).
- Kill-switch flips the sync engine to one-way (PS-authoritative) and parks all pending conflicts — loud halt, never quiet degradation (Do-Not list).

## 7. Open Items

- Wave map (provider RFP + works-council gates), archive technology, CDC tooling spike — all program decisions outside the local factory.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 16 kickoff (last queued module).
- **2026-06-11** — Review cleanup: removed unused `ChecklistError`.

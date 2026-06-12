# Meridian — complete DDL (PostgreSQL 17)

One file per bounded-context schema, generated from the live Alembic-managed
database (revision `0016`) with `pg_dump --schema-only --no-owner
--no-privileges`, so every type, primary key, unique constraint, index,
server default, and **immutability trigger** is exact.

| File | Schema | Contents |
|---|---|---|
| 01_platform.sql | platform | `audit_event` (hash-chained, append-only), `policy_decision_log`, **`forbid_mutation()` trigger function** |
| 02_workflow.sql | workflow | `workflow_instance`, `step_execution` |
| 03_integration.sql | integration | `connector_run`, `connector_credential`, `provisioning_action` |
| 04_ai.sql | ai | `ai_ledger` |
| 05_core.sql | core | `person`, `person_name`†, `national_id`, `work_eligibility`, `worker`, `assignment`†, `department`, `position` |
| 06_time_labor.sql | time_labor | `time_entry`, `time_result`, `accrual_lot` |
| 07_payroll.sql | payroll | `pay_cycle`, `pay_input_record`, `pay_result_record` |
| 08_benefits.sql | benefits | `benefit_plan`, `benefit_rate`, `enrollment` |
| 09_service_delivery.sql | service_delivery | `case`, `case_note`, `kb_article`, `delegation`, `notification_pref`, `access_grant` |
| 10_analytics.sql | analytics | `dim_worker` (SCD2), `certified_snapshot`†, `org_bridge` |
| 11_comp.sql | comp | `grade_range`†, `comp_record`† (temporal), `comp_cycle`, `cycle_line` |
| 12_recruiting.sql | recruiting | `candidate_profile`, `requisition`, `application`, `offer` |
| 13_performance.sql | performance | `goal`, `review_cycle`, `review_doc`, `calibration_adjustment`†, `checkin`, `feedback` |
| 14_learning.sql | learning | `content_item`, `assignment`, `completion_record`†, `certification` |
| 15_succession.sql | succession | `key_position`, `slate_entry`, `talent_profile`, `ninebox_placement`†, `discovery_hold` |
| 16_migration.sql | migration | `staged_record` (idempotency unique), `dq_exception`, `gate_artifact`†, `sync_conflict` |

† carries a `BEFORE UPDATE OR DELETE` immutability trigger (temporal/audit pattern).

## Build an empty database

```powershell
$env:PGPASSWORD = "meridian_dev"
createdb -h localhost -U meridian_dev meridian_new
psql -h localhost -U meridian_dev -d meridian_new -v ON_ERROR_STOP=1 -f SQL/DDL/run_all.sql
```

`01_platform.sql` must run first (it defines `forbid_mutation()`); `run_all.sql`
enforces the order. Afterwards load the demo data (`SQL/run_all.sql`).

## Relationship to Alembic (important)

`migrations/versions/` remains the **canonical** schema source — schema changes
go through Alembic, never by editing these files. If you build a database from
this DDL, align Alembic before applying future migrations:

```powershell
alembic stamp head
```

Regenerate this folder after any new migration: `python SQL/DDL/_generate.py`.

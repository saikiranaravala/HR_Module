# Meridian — PostgreSQL demo dataset

Seed data for the `meridian` database. The schema is **Alembic-managed**
(`alembic upgrade head`); for a standalone build without Alembic, the complete
table DDL lives in [`DDL/`](DDL/README.md) (`SQL/DDL/run_all.sql`), generated
from the live schema and verified column-identical. These seed scripts never
create or alter tables.
Rich enough to demonstrate every shipped feature: temporal corrections and
retro rows, payroll anomalies and held inputs, EOI-pending benefits, expat
split comp, out-of-guideline merit, AI-ranked candidates with OFCCP
dispositions, dual-record review amendments, compliance clocks and paused
leave, T3 succession slates with a gap, suppression-ready analytics, sync
conflicts and signed gate artifacts.

## Rules followed

- **Transactional**: every file is `BEGIN; … COMMIT;` — all-or-nothing.
- **Idempotent**: `ON CONFLICT DO NOTHING` on every insert; re-running a file
  is safe. `00_reset.sql` empties seeded tables for a clean reload.
- **FK-ordered**: files are numbered in dependency order; cross-references use
  fixed UUIDs declared once in `01_core_org.sql` comments.
- **Temporal pattern respected**: effective-dated tables get full
  EFFDT/EFFSEQ rows (same-day corrections as seq 1, retro rows, future rows)
  with action/reason + audit columns. History tables are insert-only — the
  database immutability triggers stay armed.
- **Synthetic PII only** (CLAUDE.md): national IDs use the invalid 900-xx SSN
  range, "encrypted" values are obvious placeholders, no real-looking bank
  data anywhere.
- **Deterministic service keys**: `comp.comp_record.comp_key` values are the
  real `uuid5("meridian:comp:<worker>:<role>")` the services compute, so
  as-of lookups work against this data.
- `platform.audit_event` is **not** seeded — it is a hash-chained append-only
  log that only application writes can extend without breaking
  `verify_chain()`. The policy decision log is likewise left to runtime.

## Load

```powershell
$env:PGPASSWORD = "meridian_dev"
psql -h localhost -U meridian_dev -d meridian -v ON_ERROR_STOP=1 -f SQL/run_all.sql
```

or file-by-file in numeric order. `run_all.sql` includes `00_reset.sql`.

| File | Contents |
|---|---|
| 00_reset.sql | Truncate all seeded tables (safe order) |
| 01_core_org.sql | Persons, names (temporal), workers, departments, positions, assignments (EFFDT/EFFSEQ incl. correction + future + retro) |
| 02_workflow_integration_ai.sql | Pending approval instances/steps (incl. role-queue fallback), connector runs + expiring credential, JML provisioning, AI ledger (ok/refused) |
| 03_time_labor.sql | Punches (incl. midnight-spanning + DST day), locked results + retro delta pair, accrual lots (FIFO, expiring carryover) |
| 04_payroll.sql | Cycles per country/state machine, held inputs, results (incl. negative-net arrears case) |
| 05_benefits.sql | Plans/rates (age-banded), enrollments: active+dependents, pending-EOI, defaulted, terminated mid-OE |
| 06_compensation.sql | Temporal ranges (incl. refresh), comp records (merit, same-day correction, expat home/host), FY26 cycle + worksheet (out-of-guideline, skip-level routing) |
| 07_recruiting.sql | Candidates (internal-confidential, do-not-rehire, GDPR-erased), reqs (pay-transparency posting), applications (AI rank+explain, OFCCP dispositions), offer version chain + accepted offer |
| 08_performance.sql | Goal cascade + version chain + orphan, review docs (AI-drafted+edited, released, amended dual record, PIP restricted, closeout), calibration lineage, check-ins (private notes), 360 feedback above/below anonymity threshold |
| 09_learning.sql | Content versions, assignments (in-progress + paused leave clock + corrupt suspend demo + contractor lightweight), completions (pinned version, import, equivalency), certifications (expiring, lapsed job-required) |
| 10_service_delivery.sql | Cases (payroll/benefits/ER-T3 + transcript), notes (internal vs employee), KB (published/stale/legal-review), delegations, notification prefs (consent, quiet hours), alumni grant + legal hold |
| 11_analytics.sql | SCD2 dimension rows (closed + open + exits + contingent), certified snapshots v1 + restated v2, org bridge |
| 12_succession.sql | Key positions (one slate gap), slates (emergency designee, stale entry), talent profiles (consent wall, interim), 9-box lineage, privileged discovery hold |
| 13_migration.sql | Staged records (idempotency key), DQ steward queue, signed gate artifact, sync conflicts (open + parked by kill-switch) |
| run_all.sql | `\ir` includes, in order |

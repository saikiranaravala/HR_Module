# Training 07 — Maintenance & Operations (Run / Support)

**Audience:** DBAs and application-support engineers who keep a deployed Meridian healthy. **Duration:** 2 days. **Prerequisites:** Training 06.

## Learning Objectives

Run the routine maintenance calendar; verify system integrity (audit chain, immutability guards, model/migration agreement); execute safe data operations; triage the five recurring incident classes with the correct playbook; know the hard lines that no incident justifies crossing.

---

## Day 1 — Routine Maintenance & Integrity

### 1.1 The maintenance calendar

| Cadence | Task | How |
|---|---|---|
| Daily | API liveness | `GET /docs` returns 200; cold-start latency is normal on free tier |
| Daily | Audit chain integrity | `GET /v1/audit/verify` → `{"intact": true, "firstBrokenSeq": null}` |
| Weekly | Full test suite against a scratch DB | pytest green = code/schema/config still agree |
| Weekly | Backup verification | Local: `pg_dump -Fc meridian`; Supabase: confirm automated backups in dashboard; **restore-test monthly**, a backup you haven't restored is a hope, not a backup |
| Per migration | Up/down/up + DDL regeneration | Training 06 §2.1; `SQL/DDL/_generate.py` |
| Monthly | Demo/test dataset refresh | `SQL/00_reset.sql` + `SQL/run_all.sql` (idempotent) |
| Monthly | Knowledge-base staleness queue | 12-month stale alerts feed copilot quality (with HR super user) |

### 1.2 Integrity verification deep-dive

**Audit chain:** every audit event carries a hash chained to its predecessor (timestamps canonicalized to UTC before hashing). `verify_chain` walks it; a non-null `firstBrokenSeq` is a **sev-1 security incident** — preserve the DB, escalate to security, do not "repair" the chain.

**Immutability guards:** row-level triggers (`platform.forbid_mutation()`) reject UPDATE/DELETE on temporal history, audit events, certified snapshots, calibration/9-box lineage, completion records, gate artifacts. Spot-check quarterly:
```sql
UPDATE succession.ninebox_placement SET potential='x' WHERE false; -- trigger must exist; a real row attempt must raise "immutable"
SELECT tgname FROM pg_trigger WHERE tgname LIKE 'immutable_%';     -- 20 triggers expected
```
**Known TRUNCATE caveat:** TRUNCATE bypasses row-level triggers by design — it's how test/reset tooling works. In production-like DBs, TRUNCATE permission on guarded tables must simply not exist.

**Model/migration agreement:** the weekly pytest run *is* the check (tests build from ORM metadata; dev DB from migrations). A mismatch is a release-blocking defect, not an ops workaround.

## Day 2 — Data Operations & Incident Playbooks

### 2.1 Safe data operations

The only sanctioned write paths are the application services. For data problems:

| Problem | Correct operation | Never |
|---|---|---|
| Wrong value entered today | Correction row (same eff-date, seq+1) via the app | `UPDATE` the row |
| Missed historical change | Retro transaction via the app (emits retro event; payroll reconciles) | Backdated `INSERT` by hand |
| Bulk load needed | Migration-factory pattern: staged, idempotent on (batch, source_key), DQ-gated | Ad-hoc `COPY` into live schemas |
| "Delete this person" (GDPR) | The domain's erasure workflow (e.g., recruiting GDPR erasure) — scoped, logged, retention-aware | `DELETE` cascade |

If someone with authority insists on direct SQL against history: the triggers will block it, and that's the system working. Escalate with this doc.

### 2.2 Incident playbooks

**P1 — Payroll cycle halted (anomaly gate / held input).** Expected behavior, not an outage: the pipeline halts loudly or proceeds provably. Triage with the payroll super user (Training 03 §2.1). Fix causes (bad input, rule version, provider file), never force past the gate — no force path exists.

**P2 — Mass permission denials.** The policy engine **fails closed**: any evaluation error → DENY. So a config/DB/connectivity fault looks like "everyone lost access." Check policy config version (`roles.yaml` load), DB connectivity, then the decision log for the failure reason. Restore the failing dependency; do not hand out roles to compensate.

**P3 — Audit chain broken.** Sev-1 security incident (see 1.2). Preserve, escalate, never repair in place.

**P4 — API up, DB unreachable.** Endpoints return RFC7807 503 problems (never fake data). Local: service `postgresql-x64-17` status. Cloud: Supabase pause state (free tier pauses after 7 idle days), then Render env var, then Supabase status page. Restore-and-verify: `/v1/audit/verify` end-to-end proves API→DB.

**P5 — Copilot giving wrong/stale policy answers.** Not a model incident: check KB staleness queue first, then whether the case-handoff (contradiction → case) is firing, then the AI ledger for the retrieved sources. Content fix > prompt fix; prompts change via the versioned registry, not hotfix.

### 2.3 Hard lines (no incident justifies)

- Disabling immutability triggers or the policy engine "temporarily"
- Direct SQL writes to temporal history, audit, or certified snapshots
- Copying production data into test/training environments (synthetic only, always)
- Adding a silent-failure dependency to the payroll path (halts loudly or proceeds provably)
- Editing the Alembic chain history (fix forward with a new revision)

---

## Competency Checklist (sign-off)

- [ ] Executes the full maintenance calendar unaided, including a restore test
- [ ] Runs and interprets audit-chain verification; states the broken-chain response
- [ ] Demonstrates correction vs retro vs staged-load decisions for three data scenarios
- [ ] Walks all five playbooks from symptom to resolution
- [ ] Explains fail-closed and why mass denials mean "fix the dependency, not the roles"
- [ ] Recites the five hard lines

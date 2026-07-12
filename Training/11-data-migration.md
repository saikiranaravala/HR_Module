# Training 11 — Data Migration Specialist (PeopleSoft → Meridian)

**Audience:** the extraction, reconciliation, and cutover team. **Duration:** 3 days. **Prerequisites:** PeopleSoft data model (PS_JOB, EFFDT/EFFSEQ), SQL; Training 03 §1.1 (temporal backbone).
**Reference:** `Specs/16-migration.md`, `TechDesignDoc/16-migration-design.md`, `src/migration/`.

## The Factory Model

Migration is a **repeatable factory**, not a one-off script: extract → stage → data-quality gates → load → reconcile → (coexistence sync) → cutover, per wave. The machinery is wave-agnostic; the wave map itself is gated by open program decisions (payroll RFP, works-council inventory) — you certify on the factory now, waves get scheduled when gates close.

## Day 1 — Extraction & Staging (MIG-1, MIG-2)

### 1.1 The PeopleSoft adapter — the one place PS exists

**PS codes never leave `extraction.py`** (Invariant #4 applied to migration). Everything downstream speaks Meridian's canonical contracts. Inside the adapter:

- **Full EFFDT/EFFSEQ history is preserved** — you are not migrating current state; you are migrating *history*. PS's effective-dating maps directly onto Meridian's temporal pattern.
- **Action-taxonomy mapping** (`config/action_mapping.yaml`): every PS action/reason maps to a canonical action. An unmapped code **halts loudly** — you add the mapping deliberately; nothing is coerced to "misc."
- **Rehire-bridging recompute:** PS rehire conventions are recomputed to Meridian's bridged original-hire-date rule, with a diff report — expect and review differences rather than assuming parity.
- **Orphan-feed discovery** flags PS records referenced by downstream feeds but absent from your extraction scope — the classic "we forgot the union sub-table" catch.

### 1.2 Staging & data quality

- **Idempotent staging on (batch, source_key)** — re-running a batch upserts, never duplicates. Re-run freely; that's the design.
- **DQ scorecards** run four rule classes with threshold gates; failures land in the **steward queue** with **fix-at-source guidance** — the default remedy is "fix it in PS and re-extract," not "patch it in staging." Staging patches erode the reconciliation baseline.
- **Mapping specs** (`config/mapping_specs.yaml`) are versioned config — field-level source→target with transforms; change control like any config release (Training 04 discipline).

**Exercise 1** — Run the demo batch twice (prove idempotency); introduce an unmapped action code (watch the loud halt); work a DQ exception through the steward queue.

## Day 2 — Reconciliation & Coexistence (MIG-3, MIG-4)

### 2.1 Reconciliation — the 99.95% gate

- **Critical-field reconciliation is computed, not sampled:** the gate requires **≥99.95% match on critical fields** before a wave may proceed, calculated over the full population.
- **Recompute triage:** every variance is classified **rule-vs-data** — did Meridian compute something differently (rule variance: investigate the rule/config), or did the data differ (data variance: back to DQ)? The variance taxonomy includes **environment-difference** (e.g., PS bug we deliberately don't replicate) — documented, signed, and accepted, not hidden.
- **Gate artifacts are immutable and signed** — reconciliation evidence is written once, DB-trigger-protected (like certified snapshots). Your go/no-go evidence cannot be quietly amended after the fact.

### 2.2 Coexistence sync (parallel-run period)

- **Field-ownership matrix per phase** (`config/ownership_matrix.yaml`): during coexistence, each field has exactly one system of record; the matrix flips ownership per cutover phase.
- **Conflict queue, 4-hour SLA:** both systems changed the same data → conflict record; stewards resolve within SLA.
- **Lag alert at >15 minutes**, and the **kill-switch degrades sync to one-way** (system-of-record keeps writing; the other becomes read-only follower) — the safe failure mode when sync itself misbehaves.

## Day 3 — Cutover & Rollback (MIG-5)

- **Go/no-go is evidence-linked and role-signed:** each checklist item links to its artifact (reconciliation gate, DQ scorecard, sync health, training certification from Training 08); named roles sign; the packet is immutable.
- **72-hour rollback window** after cutover with **retained rollback capability until 2 clean payroll cycles** complete — "clean" defined by the payroll reconciliation identity (original + retro delta = recalculated), not by absence of complaints.
- **Post-cutover data fixes** follow production rules from minute one: correction rows and retro transactions via the app — never direct SQL (Training 07 §2.1). The migration window does not suspend the invariants.
- **§7 program risks are named tests** (8/8 passing) — the risk register is executable; before each wave, the suite runs green or the wave doesn't start.

## Hard Lines

- No PS codes downstream of `extraction.py`
- No staging patches when fix-at-source is possible
- No sampling in place of computed reconciliation
- No editing gate artifacts (they're immutable — produce a new one)
- No direct-SQL "fixes" after cutover
- No wave without signed evidence and certified super users (Training 03) in that wave's countries

---

## Competency Checklist (sign-off)

- [ ] Runs extract→stage→DQ on the demo batch; proves idempotency; handles an unmapped action correctly
- [ ] Works a DQ exception fix-at-source through the steward queue
- [ ] Classifies five variances rule-vs-data-vs-environment and documents one accepted environment difference
- [ ] Explains the 99.95% computed gate and locates a signed gate artifact
- [ ] Walks the ownership matrix through a phase flip; triggers and explains the kill-switch
- [ ] Assembles a mock go/no-go packet with evidence links; states the rollback retention rule

# Deep-Dive PRD 16 — Migration & Parallel-Run Program
*Project Meridian | The program's hardest deliverable | Depends on: 03-PAY reconciliation, 15-Tech, all module readiness*

## 1. Mission & Success Metrics
Move 50K+ workers and decades of history off PeopleSoft with provable correctness — penny-perfect payroll gates, rehearsed waves, and a tested way back until the way back is no longer needed.
- Field-match ≥ 99.95% on critical fields before any population enters parallel; net-pay $0.00 variance × 3 cycles per country before authority transfer.
- Wave cutovers: 100% executed within their go/no-go criteria; rollback invocations: target 0, capability proven in rehearsal regardless.
- PeopleSoft decommission ≤ 6 months after final wave; archive query SLA met for statutory requests.

## 2. Source Analysis & Extraction
- PeopleSoft inventory workstream (month 0–3): module usage telemetry, customization census (PeopleCode/SQR/App Engine diff vs. vanilla — every customization dispositioned: config-replicate / retire / process-change), query/nVision report inventory (→ 11-ANLT disposition board), integration inventory (every inbound/outbound file and its consumer — orphan-feed discovery is guaranteed; budget for surprises).
- Extraction adapters: PS_PERSON/PERSONAL_DATA, PS_JOB (full EFFDT/EFFSEQ history), position data, PS_COMPENSATION, accrual/leave balances + plan history, benefits elections + dependent/beneficiary, payroll results (PS_PAY_CHECK et al. for archive + reconciliation), performance docs, training history (compliance-relevant minimum per 08), document attachments (with doc-type mapping + virus rescan).
- History depth (per master MIG-1, confirm month 2): job/comp full history; payroll results 7 years → queryable archive; performance 5 years; recruiting: active pipelines only + statutory applicant-flow logs.

## 3. Transform, Validate, Load (the factory)
- Mapping specs under version control (field-level source→target with transformation logic, owner, test cases) — living documents through the program; mapping change control board weekly.
- Pipeline: idempotent, restartable, environment-promotable; runs weekly (later daily) for months — engineered like a product, with its own SLOs and on-call.
- Data quality: per-domain scorecards (completeness/validity/referential/uniqueness), threshold gates, steward exception queues (in-app workflow with source-correction guidance — fix in PeopleSoft while it's authoritative, not in flight), trend dashboards (quality must improve monotonically toward each wave gate).
- Special transforms: action/reason taxonomy mapping (PS actions → Meridian taxonomy with semantic review), department-tree restructure decisions (migrate as-is; reorg later — master 01 guidance), grade structures as-is, multi-job worker reconstruction, rehire-bridging recomputation with diff report vs. PS values.

## 4. Reconciliation Workbench (MIG-3 expanded)
Count + field-match per domain per run; computed-value recomputation checks: accrual balances re-derived in Meridian rules vs. PS balances (rule-difference vs. data-difference triage), seniority dates, FTE annualizations; payroll three-way (03-PAY engine): element-level PS vs. Meridian-provider with variance taxonomy and per-country gate report auto-generation; sampling-based human audits (stratified 1% deep audits per wave by HR ops) with findings feeding mapping fixes; immutable gate artifacts (signed reports per wave entry/exit — the program's audit trail).

## 5. Parallel-Run Operations (Phases A–D detail)
- **Phase A Shadow (m1–3):** PS authoritative; nightly CDC PS→Meridian; Meridian compiles + transmits to providers in parallel-test mode (provider test environments or shadow runs per provider contract — RFP requirement); reconciliation cycles weekly; defect burn-down tracked to gate.
- **Phase B Pilot dual-entry (m3–6):** pilot populations (1 mid-complexity country + 1 US BU) transact in Meridian; **bidirectional sync service (MIG-4):** field-ownership matrix per phase (who wins per field per direction), conflict detection queue with 4-hour resolution SLA, sync-lag alerting > 15 min, kill-switch reverting to one-way; pilot exit gates: 3 penny-perfect cycles, txn error < 0.5%, CSAT ≥ 4/5, zero sev-1 sync incidents in final 30 days.
- **Phase C Waves (m6–12):** sequencing by composite score (payroll complexity, provider readiness, works-council timeline, population size); per-wave runbook: T-30 readiness review (data gate, report dispositions, training completion, country pack certification, consultation artifacts) → T-7 freeze + final sync → cutover weekend checklist (authority flip, integration re-pointing, PS read-only) → hypercare 2 cycles (command center, live error feeds, daily stand-down) → wave closure report. **Rollback:** 72-hour decision window post-cutover, rehearsed PS re-activation runbook per wave (data delta replay plan, comms templates); rollback capability retained until wave +2 clean cycles.
- **Phase D Decommission (m12–18):** PS → read-only archive (queryable store: schema-preserved extracts + a query/reporting layer for statutory/audit access, access-controlled, retention-scheduled), license/support termination on contract calendar, infra retirement with data-destruction certificates, SME knowledge-capture closeout.

## 6. Cutover Tooling & Change Management (MIG-5 expanded)
Go/no-go digital checklist (evidence-linked items, role-signed); comms engine (worker/manager wave-targeted sequences: T-30 what's-coming, T-7 actions-needed, day-1 welcome, localized); training: role-based paths in 08-LEARN with completion gates feeding readiness dashboard; readiness heatmap per wave (data, training, provider, consultation, integration re-point status); hypercare command center spec: live dashboards (case spike topics, sync conflicts, payroll exceptions), war-room roles, daily report template; feedback loop: hypercare themes → product backlog with wave-over-wave improvement tracking (wave 3 must be smoother than wave 1, measurably).

## 7. Program Risks (top 5 with owners)
Bidirectional sync (highest technical risk — dedicated squad, chaos testing, conservative pilot scale); PS SME attrition (retention incentives + knowledge-capture sprints month 0); orphan integrations discovered late (network-traffic analysis on PS hosts month 1 — find consumers nobody documented); provider test-environment fidelity gaps (contractual shadow-run requirement; variance taxonomy distinguishes env-difference); dual-run fatigue (automation-first reconciliation; backfill staffing; quarterly pacing review with authority to slow waves — schedule slips beat payroll failures, always).

## 8. Open Questions
Wave map draft (pending provider RFP + works-council inventory — target month 3). Archive technology (lightweight PS-schema warehouse vs. vendor archive product). CDC tooling for PS (GoldenGate vs. log-based alternative) — spike month 1.

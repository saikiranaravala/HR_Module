# Deep-Dive PRD 03 — Payroll Integration Hub
*Project Meridian | Depends on: 01-Core, 02-Time, 04-Benefits, 05-Comp | Feeds: ERP GL, ESS payslips, 16-Migration reconciliation*

## 1. Mission & Success Metrics
Meridian owns every payroll input and result; certified providers own statutory gross-to-net. The hub makes 30+ country payrolls operate as one observable, auditable pipeline.
- On-time transmission: 100% of cycles meet provider cut-off (alerting from T-72h).
- Input defect escape rate: < 0.1% of records require provider-side correction.
- Reconciliation automation: ≥ 95% of variances auto-classified; cycle reconciliation complete < 4h after results receipt.
- Parallel-run gate: 3 consecutive cycles per country with $0.00 net variance vs. PeopleSoft.

## 2. Canonical Payroll Data Contract (CPDC)
Versioned schema (semver; additive minor changes only mid-year). Domains:
- WorkerPayProfile: ids, legal entity, pay group, tax locale(s), contract type, statutory classifications.
- EarningElements / DeductionElements: code (canonical dictionary mapped to provider codes), amount-or-rate, units, period, cost allocation, retro flag + original-period pointer, taxability metadata.
- TimeResults (from TIME snapshot), AbsencePayInstructions (phase-based, e.g., statutory maternity rates), BenefitDeductions (from BEN, incl. imputed income), Garnishments (order id, type, priority, formula parameters), TaxElections (W-4 fields, equivalents), Banking (splits), OneTimePayments (bonus, awards with grossed-up flag).
- **Canonical element dictionary:** governed catalog (~400 elements expected) with per-country activation; provider mapping tables maintained per adapter; no provider code ever appears upstream of the adapter layer.

## 3. Adapter Framework
- Adapter = transform (CPDC→provider format) + transport (API or SFTP/PGP) + acknowledgment parser + results parser + error-code normalizer.
- **Conformance test kit:** golden-file suite per provider (≥ 200 scenario records: new hire mid-period, retro, multi-state, garnishment stack, leave phases…). Adapter cannot ship < 100% pass.
- **Initial portfolio (pending RFP, §Open Qs):** US/CA: ADP WFN or Dayforce; multi-country aggregator (ADP GlobalView/Celergo or Safeguard/CloudPay pattern) for long-tail countries; strategic locals where aggregators are weak (e.g., IN: greytHR/ADP India evaluation; JP local bureau). Target: ≤ 90 days contract→first parallel cycle (PAY-9).
- Provider SLA monitoring: ack latency, error rates, result-delivery punctuality — scorecards feeding vendor management.

## 4. Cycle Orchestration State Machine
Draft → Inputs-Compiled (snapshot: immutable input set with hash) → Validated → Approved (payroll ops sign-off, 4-eyes for cycles > configurable gross threshold) → Transmitted → Provider-Ack → Results-Received → Reconciled → GL-Posted → Payslips-Published → Closed.
- Each transition: actor, timestamp, artifact links; SLA timers per state with escalation; dashboard per country/pay-group with traffic-light board for the global payroll calendar (all cycles visible on one screen).
- **Off-cycle runs:** same machine, expedited SLAs; termination final-pay auto-instantiates an off-cycle when country deadline < next regular cycle.
- **Acceptance:** any record traceable end-to-end (UI change → CPDC field → provider file line/API payload → result line → GL line → payslip) via correlation ID in < 30 s lookup.

## 5. Pre-Payroll Validation Gate (PAY-3 expanded)
Three layers, all evaluated on the compiled snapshot:
1. **Structural:** schema, mandatory-by-country fields, referential integrity, banking prenote status.
2. **Business rules:** new-hire completeness checklist, retro sanity (delta ≤ configurable % of original), garnishment-priority consistency, leave-phase/pay alignment, FTE×salary coherence.
3. **AI anomaly scoring** (see 14-AI): variance vs. worker's trailing 6-cycle distribution, peer-group outliers (same grade/location), risky-pattern flags (bank change within 7 days of payday, duplicate bank accounts across workers, first-cycle-after-rehire). Explainable score + top factors into the review queue.
Severity model: BLOCK (cannot transmit) / HOLD-RECORD (record excluded, rest proceeds, exclusion logged + retro auto-queued) / WARN (transmit, tracked).

## 6. Results, Payslips, GL
- Results ingestion validates: per-element sums, net = gross − deductions identity, headcount match vs. transmitted set (any provider-added/dropped record is a critical alert).
- Payslip service: native render from result data (templated per country with statutory mandatory fields registry: e.g., FR bulletin line requirements, DE Entgeltabrechnung items); provider PDF stored as statutory artifact where law requires provider-issued doc; year-end docs (W-2, T4, P60, Form 16) ingested + indexed to worker doc record.
- GL engine: mapping matrix (element × cost allocation → account/segment), balancing validation (debits=credits per entity per cycle), accrual journals for split fiscal periods (day-weighted), reversal automation; journal API/file to ERP with posting acknowledgment tracking.
- Employer-cost analytics feed: fully loaded cost per worker per period → 11-Analytics.

## 7. Reconciliation Engine
- Modes: (a) cycle-over-cycle self-variance, (b) input-vs-result coherence, (c) **parallel-run three-way** (Meridian-provider vs. PeopleSoft) at element level.
- Variance classification taxonomy: timing, mapping, rate-table version, rounding, population diff, true defect — ML-assisted auto-classification with human confirmation feeding the classifier.
- Workbench: drill from country total → pay group → worker → element → input lineage; bulk annotation; cutover-gate report auto-generated per country (the Phase B/C exit artifact).

## 8. Controls & Compliance
SOX key controls catalog (input approval, change management on mappings, segregation: no user may both edit comp and approve cycle); garnishment legal-response tracking; payroll data residency: CPDC PII minimization per provider DPA; bank-detail access: break-glass only with dual authorization.

## 9. Events & APIs
Events: paycycle.state.changed, payslip.published (drives ESS notification), payroll.exception.raised, gl.posted. APIs: GET /pay-cycles/{id}/status; GET /workers/{id}/payslips; POST /off-cycles; reconciliation report endpoints for 16-Migration tooling.

## 10. Edge Cases Register
Mid-cycle legal-entity transfer (two providers, split period, YTD handover rules per country); negative net (deduction stack > gross — arrears policy engine); deceased-worker final pay (beneficiary payee, tax treatment); multi-state US workers (allocation % to provider); currency redenomination/contract FX for expat split pay; provider outage at cut-off (contingency runbook: pay-as-last-cycle authorization flow with true-up).

## 11. Open Questions
Provider RFP outcome drives adapter order (decision month 2). Payslip native-render legal review per country (some require provider-form). Treasury integration for funding confirmations — in scope for hub or ERP-side?

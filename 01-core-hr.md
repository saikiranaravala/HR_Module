# Deep-Dive PRD 01 — Core HR & Workforce Administration
*Project Meridian | Depends on: 12-Platform, 15-Tech | Feeds: every other module*

## 1. Mission & Success Metrics
The single global system of record for person, employment, position, and organization data. Every other module is a consumer.
- Data accuracy: ≥ 99.9% critical-field accuracy (sampled audits); zero duplicate active person records.
- Transaction cycle time: standard job change initiated-to-effective processing < 24h (vs. multi-day PeopleSoft baseline).
- 100% of lifecycle events emit consumable domain events within 60 seconds of commit.

## 2. Data Model (detailed)

### 2.1 Person (one per human, globally unique)
| Entity | Key fields | Notes |
|---|---|---|
| Person | person_id (UUID), legal_name[] (effective-dated, multi-script: Latin + native script for JP/CN/IN), preferred_name, dob, gender + self-described gender identity (separate, access-tiered), marital_status, nationality[] | Name parts vary by country (given/middle/family vs. patronymic); store structured + formatted |
| NationalID | type (per-country registry: SSN, SIN, Aadhaar, PAN, NI, BSN…), value (field-encrypted), issue/expiry, verification_status | Country-specific checksum validation; masked display with reveal-audit |
| Address | type (home/mailing/host), country-specific structured fields, geo-coordinates, effective dates | Drives tax locale; address change emits `worker.tax_locale.maybe_changed` |
| Contact | phones/emails (personal/work), preferred channel, verification status | Work email provisioned via IdP event round-trip |
| EmergencyContact, Dependent | relationship, dob, shared-address flag; dependent carries benefits-eligibility attributes (student status, disability) | Dependent verification doc workflow |
| WorkEligibility | document type (I-9 docs, visa class, work permit), expiry, remote-verification flag | Expiry alerts at 90/60/30 days to employee+HR; blocking rule: cannot extend assignment past permit expiry |
| BankAccount | country format (ABA/IBAN/IFSC…), split rules (%, fixed, remainder), prenote status | Field-encrypted; change triggers fraud heuristics (see 14-AI) |

### 2.2 Employment & Assignment
- **Worker** = one employment relationship (person × legal entity). Multi-job: person may have N concurrent Workers. Fields: worker_id, person_id, legal_entity, hire_date, original_hire_date (rehire bridging), seniority_dates[] (rule-computed, overridable with audit), worker_type (employee/contingent/intern/pensioner), status (active/leave/suspended/terminated).
- **Assignment** (effective-dated, sequenced): position_id or job_code, department, location, manager_assignment_id, FTE, standard_hours, work_schedule_id, pay_group, union_code, probation end, comp snapshot link. Every row: effective_date, sequence, action, reason, source_channel, created_by.
- **Action/Reason taxonomy**: ~25 actions × configurable reasons; reason codes carry analytics semantics (regrettable flag on termination reasons) and statutory mappings (e.g., FR contract-type codes).

### 2.3 Position & Job Catalog
- Position: position_id, job_code, dept, location, reports_to_position, FTE_budget, headcount_budget (single/pooled), comp_budget, status (proposed/approved/active/frozen/inactive), funding splits (cost center %, validated to 100%).
- JobProfile: code, family, level, profile content (summary, responsibilities, qualifications, competencies[] with proficiency targets), grade map per country, FLSA, EEO category, hazard/medical-surveillance flags (drives LEARN compliance assignment).
- Vacancy logic: position headcount minus active incumbents = openings; one-click requisition (REC) from vacant position.

### 2.4 Organization
- LegalEntity (registrations, tax IDs, statutory representatives), BusinessUnit, Department (tree, effective-dated moves with subtree cascade preview), Location (address, time zone, holiday calendar, OSHA establishment flag), CostCenter (ERP-mastered, read-only here), UnionAgreement (coverage rules, CBA document link to AI corpus).

## 3. Key Workflows (specified)

### 3.1 Hire (REC handoff or direct)
1. Pre-hire record from offer accept (REC) or manual entry → duplicate check (fuzzy: name+DOB, national ID exact) → match found ⇒ rehire path with service bridging rules.
2. Country onboarding checklist instantiated (docs, statutory forms: W-4 wizard, UK starter checklist, IN PF nomination).
3. Day-1 trigger: status active → events to IdP (SCIM create), badging, payroll hub (new-hire record), benefits (eligibility evaluation).
- **Acceptance:** hire with complete data processes < 5 min end-to-end; missing-statutory-doc blocks payroll inclusion, not system access.

### 3.2 Transfer/Promotion
Initiated by MSS/HRBP → guided flow (new position/dept/manager/comp proposal with guideline display) → approval matrix (cross-BU transfers require both-side approval; comp change beyond guideline adds comp-team step) → future-dated commit → automatic events at effective date.
- **Edge cases:** transfer across legal entities = termination+rehire in some countries (DE) vs. continuous in others — country rule decides pattern, UI presents as a single "transfer"; pending timesheets/approvals re-route to new manager with notification; open performance docs prompt review-transfer decision.

### 3.3 Leave of Absence
Type catalog per country (FMLA, parental variants, sabbatical, jury, military) with entitlement rules → request (ESS) or HR-initiated → eligibility auto-check (tenure, hours-worked for FMLA 1,250-hr test) → approval → status sub-state (paid/unpaid phases on a timeline, e.g., UK maternity: 6wk @90% → 33wk statutory) → payroll hub instructions per phase → return-to-work confirmation with fitness-doc capture where required.

### 3.4 Termination
Initiation (MSS or HR) → reason + last-day + rehire-eligibility → checklist (asset, knowledge transfer) → final-pay instruction with country deadline rule (CA: same day for involuntary; MX: finiquito calc data) → access revocation event scheduled at effective time (≤15 min SLA) → COBRA/continuation event → exit survey.
- **Death-in-service:** distinct sensitive flow: locks ESS, routes beneficiary tasks, suppresses automated communications.

### 3.5 Mass Transactions / Reorg Studio
Upload or org-chart drag-drop → validation (manager loops, orphaned positions, security-scope changes) → impact simulation report (payroll routing changes, benefits eligibility changes, approval-chain changes) → staged approval → batch commit with progress + per-row error queue → post-commit event storm rate-limited to protect consumers.
- **Acceptance:** 5,000-worker dept move commits < 15 min; rollback available until commit.

## 4. Compliance Sub-System
- US: EEO-1 (component 1 file generation + history), VETS-4212, OSHA incident capture (300/300A/301 with privacy cases handling), state new-hire reporting feeds, ACA hours feed to BEN.
- Country packs as content: each pack = field extensions, validation rules, statutory reports, document templates, retention schedule. Pack versioning with regulatory-change release notes. Gate: country pack certified before that country's pilot.
- Point-in-time engine: `as_of` parameter on all queries; reconstructs org tree + population snapshot; powers audit/litigation responses.

## 5. Events & APIs (contract excerpts)
Events: worker.hired, worker.rehired, assignment.changed (typed change set), worker.leave.started/ended, worker.terminated, position.created/changed, department.restructured, person.pii.updated (minimal payload + pull pattern for PII).
APIs: GET /workers/{id}?as_of=…; GET /org/departments/{id}/tree?depth=…; POST /assignments:simulate (what-if without commit); batch endpoints with async job pattern.

## 6. Edge Cases Register (must-pass test scenarios)
Retro hire-date correction after first payroll; concurrent multi-country jobs with treaty tax flags; rehire with prior negative PTO balance; future-dated promotion overlapping a pending transfer (sequence conflict resolution UI); department inactivation with active incumbents (blocked with guided re-home); name change with legal-doc verification mid payroll cycle; minor employees (work-permit rules, hour restrictions feeding TIME).

## 7. Open Questions
Contingent workers: full records vs. lightweight profiles (recommend lightweight + VMS link in v1). Global grade harmonization before or after migration (recommend after — migrate as-is, harmonize as a separate program).

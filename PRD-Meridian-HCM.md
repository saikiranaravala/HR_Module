# Product Requirements Document — Project Meridian
## AI-Native Human Capital Management Platform (PeopleSoft HCM Replacement)

| | |
|---|---|
| **Version** | 1.0 Draft |
| **Date** | June 2026 |
| **Status** | For stakeholder review |
| **Scope** | Full-suite HCM, 50,000+ employees, global, AI-native |
| **Strategy** | Replace Oracle PeopleSoft HCM 9.2 via 6–12 month parallel run |

---

## 1. Executive Summary

Project Meridian is a ground-up, AI-native Human Capital Management platform that replaces the organization's Oracle PeopleSoft HCM estate. It delivers the full functional breadth of PeopleSoft — Core HR, Position Management, Time & Labor, Payroll (via a provider-integration hub), Benefits, Compensation, Recruiting, Performance, Learning, and Succession — re-architected as cloud-native microservices with AI agents, copilots, and retrieval-augmented knowledge embedded in every workflow rather than bolted on.

**Why replace rather than upgrade:** PeopleSoft's component-processor architecture, PeopleCode customization debt, and on-premise cost structure make it progressively more expensive to operate and impossible to make AI-native. Oracle's own strategic investment has shifted to Fusion Cloud HCM; remaining on PeopleSoft means paying maintenance for a platform in managed decline.

**Three strategic bets:**

1. **Payroll as an orchestration problem, not a calculation problem.** Rather than rebuilding gross-to-net engines for 30+ jurisdictions (the single largest cause of failed HCM builds), Meridian builds a *Payroll Integration Hub* that orchestrates certified local providers (ADP, SD Worx, Ceridian/Dayforce, local bureaus) behind a unified employer-of-record data contract. Meridian owns the system of record; providers own statutory calculation.
2. **AI-native, not AI-added.** Every persona gets an embedded copilot; every document corpus (policies, contracts, collective agreements) is queryable via retrieval-augmented generation; high-volume workflows (case deflection, job description drafting, anomaly detection in payroll pre-checks) are agentic from day one — with human-in-the-loop controls and a full AI audit trail.
3. **Parallel run as the trust mechanism.** A 6–12 month dual-run period in which PeopleSoft remains authoritative while Meridian shadows every transaction, with automated reconciliation reporting down to the pay-element level, is the non-negotiable de-risking strategy for a 50K-employee cutover.

**Success criteria at exit of parallel run:**

- 100% of in-scope employee records migrated with field-level reconciliation ≥ 99.95% match rate.
- Three consecutive payroll cycles per country with net-pay variance of $0.00 (penny-perfect) between PeopleSoft and Meridian-orchestrated results before that country cuts over.
- ESS/MSS adoption ≥ 85% of active workforce within 90 days of cutover.
- HR case volume reduced ≥ 30% via AI self-service deflection.
- PeopleSoft license, hosting, and support contracts fully decommissioned within 6 months of final cutover.

---

## 2. Goals, Non-Goals, and Guardrails

### 2.1 Goals

- **G1 — Functional parity plus:** Match every PeopleSoft module in production use today, then exceed it in usability, mobile access, and intelligence.
- **G2 — Single global system of record:** One employee master, one position structure, one org model, spanning all countries and legal entities.
- **G3 — Statutory compliance by design:** EEO-1, OSHA 300/300A/301, GDPR, country labor law, and works-council requirements are first-class product features, not reporting afterthoughts.
- **G4 — Consumer-grade experience:** Mobile-first ESS/MSS; any common task completable in under 60 seconds on a phone.
- **G5 — AI throughout:** Copilots, agents, and RAG knowledge embedded in every module, governed by a central AI policy layer.
- **G6 — Total cost of ownership reduction:** ≥ 35% reduction in run-rate cost versus the PeopleSoft estate (licenses + hosting + DBA/admin labor + customization maintenance) within 24 months of cutover.

### 2.2 Non-Goals (v1)

- Building native gross-to-net payroll calculation engines (delegated to certified providers via the hub).
- Replacing the Finance/ERP general ledger (Meridian integrates; it does not replace).
- Contingent-workforce VMS (vendor management) — integrate with existing VMS in v1, evaluate native build in v3.
- Commercializing the platform externally (revisit after internal stabilization).

### 2.3 Guardrails

- No AI agent may commit a financial or employment-status transaction without explicit human approval (see §8.5, AI Governance).
- No country goes live on Meridian payroll orchestration without three penny-perfect parallel cycles.
- All personally identifiable data remains within approved data-residency boundaries per country (see §9.4).
- Customizations are configuration-only: no customer-specific code forks. Extensibility happens through the rules engine, workflow designer, and API layer.

---

## 3. Users and Personas

| Persona | Population (est.) | Primary surface | Top jobs-to-be-done |
|---|---|---|---|
| **Employee** | 50,000+ | Mobile app / web ESS | View payslip, request PTO, update personal data, enroll in benefits, find policies |
| **People Manager** | ~6,000 | MSS web + mobile | Approve time/leave, initiate job changes, view team analytics, run performance cycles |
| **HR Business Partner** | ~250 | HR workspace | Case management, employee relations, org changes, reporting |
| **HR Operations / Shared Services** | ~150 | Admin console + case queue | Data corrections, mass transactions, onboarding processing, audits |
| **Payroll Operations** | ~60 | Payroll hub console | Pre-payroll validation, provider file orchestration, reconciliation, off-cycle runs |
| **Recruiter** | ~120 | ATS workspace | Requisition management, pipeline review, interview scheduling, offers |
| **Compensation Analyst** | ~25 | Comp planning workspace | Cycle administration, market benchmarking, equity administration |
| **Benefits Administrator** | ~30 | Benefits console | Plan configuration, open enrollment, carrier file management, evidence-of-insurability |
| **L&D Administrator** | ~40 | LMS console | Catalog management, compliance training assignment, certification tracking |
| **System Administrator / IT** | ~20 | Platform admin | RBAC, integrations, tenant config, audit, observability |
| **Executive / Workforce Planner** | ~200 | Analytics workspace | Headcount, attrition, cost modeling, succession risk, DEI dashboards |

---

## 4. Functional Requirements — Module Specifications

Requirement IDs use the pattern `<MODULE>-<number>`. Priority: **P0** = required for parallel-run start, **P1** = required for cutover, **P2** = fast-follow within 6 months of cutover.

### 4.1 Core HR & Workforce Administration (CORE)

The system of record for all person, job, and organizational data. This is the foundation every other module reads from; it must be live first and is the anchor of the parallel run.

**Person model**

- **CORE-1 (P0):** Global person record with effective-dated history for every attribute: legal name(s), preferred name, demographics, national IDs (SSN, Aadhaar, NI number, etc. — per-country ID types with country-specific validation and encryption), contact details, addresses with country-specific formats, emergency contacts, dependents/beneficiaries, work eligibility documents (I-9, visa/permit with expiry alerting), bank details (multi-account split deposits), and disability/veteran self-identification (US) with strict access controls.
- **CORE-2 (P0):** Effective dating on all records: every change carries effective date, sequence number, action/reason code, and full before/after audit capture. Future-dated transactions execute automatically; retroactive changes trigger downstream recalculation events (notably to the Payroll Hub and Benefits).
- **CORE-3 (P0):** A person may hold **multiple concurrent jobs** (multi-job/multiple employment relationships), including across legal entities and countries — a notorious PeopleSoft strength that must not regress. Each employment relationship carries its own compensation, manager, FTE, and payroll routing.
- **CORE-4 (P0):** Person matching and duplicate prevention on hire/rehire (fuzzy match on name + DOB + national ID), with rehire bridging of prior service dates for benefits/seniority rules.

**Job & position management**

- **CORE-5 (P0):** Full position management: positions exist independently of incumbents, carry job code, department, location, reports-to position, FTE, budgeted headcount and budgeted compensation, and effective-dated history. Support both position-managed and job-managed (positionless) populations per business unit — global enterprises always have both.
- **CORE-6 (P0):** Job catalog: job codes, job families/functions, standard job profiles (description, qualifications, competencies), salary grade/range mapping per country/region, FLSA classification (US), and EEO/AAP job categories.
- **CORE-7 (P0):** Organizational structures: legal entities (with registration numbers, tax IDs), business units, departments (tree-structured, effective-dated), locations (with geo data for tax and statutory reporting), cost centers (synchronized with ERP GL), and union/works-council coverage mapping.
- **CORE-8 (P0):** Multiple concurrent hierarchies: supervisory (reports-to), matrix/dotted-line, HR support model (HRBP coverage), and security hierarchy may all differ. Org chart visualization with drill-down, export, and what-if modeling (drag-and-drop reorg simulation producing a transaction batch for approval).

**Workforce lifecycle**

- **CORE-9 (P0):** Action/reason framework covering the complete lifecycle: hire, rehire, transfer, promotion, demotion, lateral move, FTE change, location change, manager change, leave of absence (paid/unpaid, statutory types per country: FMLA, parental leave variants, sabbatical, military), suspension, termination (voluntary/involuntary with reason taxonomy), retirement, and death-in-service. Every action is workflow-routed per configurable approval matrices.
- **CORE-10 (P0):** Mass transaction engine: bulk department moves, mass manager changes, reorganizations, acquisitions onboarding — with preview, validation, simulation of downstream impact (payroll, security, benefits eligibility), staged commit, and one-click rollback before commit.
- **CORE-11 (P1):** Onboarding orchestration: pre-boarding portal (before day one), task checklists routed to employee/manager/IT/facilities, document collection with e-signature, provisioning triggers to ITSM/IdP, and I-9/right-to-work verification workflows (E-Verify integration for US).
- **CORE-12 (P1):** Offboarding orchestration: termination checklist, asset recovery, deprovisioning triggers (same-day access revocation to IdP), final-pay instruction to Payroll Hub respecting state/country final-pay deadline rules, exit survey, and COBRA/benefits-continuation event generation.

**Compliance & statutory reporting**

- **CORE-13 (P1):** US: EEO-1 Component 1 generation, VETS-4212, OSHA 300/300A/301 recordkeeping with incident capture workflow and February 1 posting pack, ACA 1094-C/1095-C data feeds, state new-hire reporting.
- **CORE-14 (P1):** Per-country statutory packs delivered as configuration content (not code): e.g., India (PF/ESI/gratuity data capture, Shops & Establishments registers), UK (right-to-work, gender pay gap reporting), EU (works-council data interfaces, whistleblower-directive case separation), with a country-pack roadmap covering 100% of operating countries before each country's cutover.
- **CORE-15 (P1):** Point-in-time reporting: any report or API can be executed "as of" any historical date, reconstructing the org and population exactly as it was — required for audits and litigation holds.

### 4.2 Time & Labor (TIME)

- **TIME-1 (P0):** Configurable timesheets: punch (clock in/out via web, mobile with geofencing, and physical clock integration), elapsed, and exception-based (auto-filled from schedule, employee reports exceptions only). Population-level policy assignment determines which model applies.
- **TIME-2 (P0):** Rules engine for time calculation: overtime (daily/weekly/consecutive-day rules, e.g., California daily OT and double-time; EU Working Time Directive limits), shift differentials, on-call/call-back pay, meal/rest-break premiums and penalty pay, rounding rules, and holiday calendars per country/site. Rules are versioned, effective-dated, testable configuration — with a rule simulator that replays historical timesheets against draft rules.
- **TIME-3 (P0):** Absence management: accrual engines (hours-worked-based, tenure-banded, grant-based), carryover and cap rules, country statutory leave types, leave request/approval with team-calendar conflict view, negative-balance policies, and integration of absences into payroll-period results.
- **TIME-4 (P1):** Scheduling: shift templates, rotation patterns, schedule publication with notification, open-shift offer/claim, swap requests with rule validation (qualification, rest-period, and overtime checks), and labor-demand-driven schedule suggestions (P2 for the AI-assisted version).
- **TIME-5 (P0):** Project/cost tracking: time charged to projects, tasks, and cost centers with validation against the ERP project master; approval routing may differ for project time vs. attendance time.
- **TIME-6 (P0):** Exception management dashboard: missed punches, unapproved time, rule violations, and excessive-hours alerts, with bulk resolution tools and escalation SLAs. Payroll-period lock prevents edits after sign-off; post-lock changes route as retro adjustments to the Payroll Hub.

### 4.3 Payroll Integration Hub (PAY) — provider-orchestration model

Meridian does **not** calculate statutory gross-to-net. It is the authoritative source of every payroll *input*, the orchestrator of provider processing, and the system of record for every payroll *result*.

- **PAY-1 (P0):** Canonical payroll data contract: a versioned, provider-agnostic schema covering worker identity, employment, earnings elements, deduction elements, time results, absence results, benefits deductions, garnishments, tax elections, banking, and retro adjustments. Per-provider adapters map the canonical contract to each provider's format (API where available — e.g., ADP Workforce Now/GlobalView APIs — or SFTP file specs where not).
- **PAY-2 (P0):** Pay-cycle orchestration: per country/pay-group calendars; automated extract → transmit → acknowledge → error-handling → result-ingest pipeline with state machine per cycle (Draft → Validated → Transmitted → Provider Processing → Results Received → Reconciled → Posted → Closed). Every state transition is auditable and alert-instrumented.
- **PAY-3 (P0):** Pre-payroll validation gate: 100% of outbound records pass configurable validation (missing bank details, mid-period retro flags, new-hire completeness, out-of-range variance vs. prior period). AI anomaly detection scores each record (see §8); records above threshold are queued for human review before transmission. **Nothing transmits with blocking errors.**
- **PAY-4 (P0):** Results ingestion: gross-to-net results, payslip data, employer-cost elements, and GL distribution detail ingested per cycle; Meridian renders payslips natively in ESS (provider payslip PDF retained as the statutory artifact where required by country law).
- **PAY-5 (P0):** Reconciliation engine: automated three-way comparison (Meridian inputs vs. provider results vs. — during parallel run — PeopleSoft results) at pay-element granularity, with variance classification, tolerance configuration (target: $0.00 net-pay tolerance for cutover gating), drill-down workbench, and cycle-over-cycle trend reporting.
- **PAY-6 (P0):** GL posting: configurable mapping from pay elements × cost centers to GL accounts; journal generation to ERP with balancing validation; accrual journals for period-end when pay periods cross fiscal periods.
- **PAY-7 (P1):** Garnishment/court-order administration: order capture, priority sequencing rules, disposable-income data to providers, lifecycle tracking, and agency correspondence record-keeping.
- **PAY-8 (P1):** Off-cycle and final-pay orchestration: on-demand runs for terminations (meeting same-day/72-hour statutory deadlines where applicable), corrections, and bonus runs, through the same validated pipeline.
- **PAY-9 (P1):** Provider portability: adding or replacing a country provider requires only a new adapter and country pack — target ≤ 90 days from contract to first parallel cycle for a new provider. No provider lock-in at the data-model level.

### 4.4 Benefits Administration (BEN)

- **BEN-1 (P0):** Plan configuration: medical/dental/vision, life and AD&D (basic, supplemental, spousal/child), disability (STD/LTD), retirement (401(k)/Roth with match formulas, pension scheme data capture for DB plans, country variants such as India PF/superannuation, UK auto-enrolment with qualifying-earnings logic), FSA/HSA/dependent-care/commuter accounts, and voluntary benefits — all with effective-dated plan years, rate tables (age-banded, salary-banded, smoker status), and employer/employee cost splits.
- **BEN-2 (P0):** Eligibility engine: rule-based eligibility (employment class, FTE, location, union, waiting periods, ACA measurement/stability periods with look-back method support), continuous evaluation on every Core HR event, and automated event generation (gain/loss of eligibility).
- **BEN-3 (P0):** Life events and open enrollment: configurable qualifying-event types with documentation requirements and verification workflow; annual open enrollment with side-by-side plan comparison, decision-support recommendation (AI-assisted, see §8), dependent verification, evidence-of-insurability routing to carriers, and confirmation statements.
- **BEN-4 (P0):** Carrier and vendor connectivity: outbound enrollment files (EDI 834 and carrier-proprietary formats) on carrier-specific calendars, error/discrepancy ingestion, and retirement-provider payroll-deduction feeds — with the same adapter pattern as the Payroll Hub.
- **BEN-5 (P1):** COBRA/continuation event generation and administrator handoff; ACA 1095-C data assembly; imputed-income calculation feeds (GTL over $50K, domestic-partner coverage) to the Payroll Hub.

### 4.5 Compensation Planning (COMP)

- **COMP-1 (P0):** Compensation foundation: salary structures (grades, ranges, geographic differentials), pay components (base, allowances with country taxes treatment metadata, recurring/one-time), compa-ratio and range-penetration computed on every comp record.
- **COMP-2 (P1):** Cycle management: annual merit/bonus/equity cycles with budget allocation cascading down the manager hierarchy, eligibility rules, proration (hire date, leave, FTE changes), guideline matrices (performance × compa-ratio), out-of-guideline justification and approval, currency handling (plan in local, budget in corporate currency with locked cycle FX rates), and calibrated worksheet roll-up/roll-down.
- **COMP-3 (P1):** Equity administration: grant data capture (options, RSUs, ESPP), vesting schedule tracking, integration with cap-table/equity platforms (e.g., Shareworks, Carta), and taxable-event feeds to the Payroll Hub at vest/exercise.
- **COMP-4 (P2):** Market benchmarking: survey data import (Mercer/Radford/WTW job matching), market-reference-point analytics, and pay-equity analysis workbench (regression-based, protected-class gap analysis with remediation modeling) supporting EU Pay Transparency Directive obligations.
- **COMP-5 (P1):** Total rewards statement: employee-facing annual statement aggregating cash, bonus, equity, employer benefits cost, and retirement contributions.

### 4.6 Recruiting & Onboarding (REC)

- **REC-1 (P1):** Requisition lifecycle: creation from position (inheriting job profile and budget validation), approval routing, posting to career site and job boards (Indeed/LinkedIn via standard feeds), internal-mobility-first posting windows, and agency portal submission with duplicate-ownership resolution.
- **REC-2 (P1):** Candidate experience: branded career site (responsive, WCAG 2.2 AA), ≤ 5-minute apply flow with resume parsing (multilingual), candidate portal with status visibility, and GDPR-compliant consent and retention management.
- **REC-3 (P1):** Pipeline management: configurable stage workflows per requisition type, AI-assisted screening that *ranks and explains* but never auto-rejects (see §8.5 and NYC Local Law 144 / EU AI Act high-risk obligations), knockout questions, structured interview kits with competency-based scorecards, panel scheduling with calendar integration and self-schedule links, and assessment-vendor integrations.
- **REC-4 (P1):** Offer management: offer templates per country with compensation validation against ranges, approval matrices, e-signature, and automatic hire-event handoff to Core HR onboarding (no re-keying — the single biggest PeopleSoft-era pain point to eliminate).
- **REC-5 (P2):** Recruiting analytics: time-to-fill, source effectiveness, pipeline pass-through and adverse-impact monitoring by stage, recruiter capacity dashboards.

### 4.7 Performance Management (PERF)

- **PERF-1 (P1):** Goal management: cascading goals (company → org → team → individual) with alignment visualization, OKR or MBO style per business-unit configuration, weighting, and mid-cycle revision with audit history.
- **PERF-2 (P1):** Review cycles: configurable templates (annual, semi-annual, probationary, PIP), self/manager/skip-level inputs, competency assessment tied to job-profile competencies, rating scales with optional forced-distribution guidance, calibration sessions with side-by-side talent-grid views and adjustment audit trails, and release/acknowledgment workflow.
- **PERF-3 (P1):** Continuous performance: check-in scheduling and notes, real-time feedback (request/give, praise walls), and 360-degree feedback campaigns with anonymity thresholds and rater-selection approval.
- **PERF-4 (P2):** AI writing assistance: draft self-assessments and manager narratives from goal data and feedback history (clearly attributed, fully editable); bias-language linting on manager reviews before submission.

### 4.8 Learning & Development (LEARN)

- **LEARN-1 (P1):** Course catalog and delivery: instructor-led (session/roster/waitlist/attendance management), e-learning (SCORM 1.2/2004 and xAPI runtime), external content-provider integration (LinkedIn Learning, Coursera), curricula/learning paths, and manager assignment with due dates.
- **LEARN-2 (P0 for compliance training):** Compliance training engine: rule-based assignment by population (role, location, regulation), recurrence (annual harassment-prevention training per state law, safety certifications), escalating reminders, manager and compliance-officer dashboards, and audit-ready completion evidence. *This is P0 because regulatory training continuity cannot lapse during migration.*
- **LEARN-3 (P1):** Certification and license tracking: external certifications with expiry alerting, renewal workflows, and job-requirement validation (alert when an incumbent's required license lapses).
- **LEARN-4 (P2):** Tuition reimbursement: application, approval, grade-evidence submission, reimbursement instruction to Payroll Hub with taxability metadata, and clawback-agreement tracking.
- **LEARN-5 (P2):** AI skills inference: skill-profile suggestions from job history, learning records, and project data; personalized learning recommendations mapped to career-path gaps.

### 4.9 Succession & Career Planning (SUCC)

- **SUCC-1 (P1):** Key-position designation with criticality scoring; succession slates per position with readiness ratings (ready-now / 1–2 years / 3+ years) and incumbent-risk flags (retirement eligibility, flight risk).
- **SUCC-2 (P1):** Talent profiles and 9-box: performance × potential grids fed by PERF data, talent-review meeting mode (live grid manipulation with decision audit), and development-plan linkage to LEARN.
- **SUCC-3 (P2):** Career pathing: employee-visible career lattices built from job-catalog adjacency, skill-gap analysis against target roles, and internal-opportunity matching (gigs, mentorships, open requisitions).
- **SUCC-4 (P1):** Strict confidentiality model: succession data is the most sensitive non-payroll data in the system; access limited to designated talent roles and the executive chain, excluded from standard manager views, and fully audit-logged on read (not just write).

### 4.10 Employee & Manager Self-Service (ESS/MSS)

- **ESS-1 (P0):** Employee self-service (web + native iOS/Android): payslips and year-end tax documents (W-2, P60, Form 16, etc.), tax-withholding elections (US federal/state W-4 wizards with provider routing), direct-deposit management with micro-deposit or instant verification and fraud-pattern alerting (bank-change + payday proximity), personal data updates (workflow-gated where statutory), PTO request with balance projection ("if I take these days, my balance on Dec 31 will be…"), timesheet entry/punch, benefits enrollment, company directory with org chart, document e-signature inbox, and expense submission (or deep-link to the ERP expense tool — decision required, see §13 Open Questions).
- **MSS-1 (P0):** Manager self-service: unified approval inbox (time, leave, job changes, comp, requisitions) with delegation and out-of-office rules, team calendar and absence heat-map, initiate transactions (transfer, promotion, comp change with guideline display, termination initiation), team dashboards (headcount, turnover, time compliance, performance-cycle status), and "position to fill" one-click requisition creation.
- **ESS-2 (P0):** HR Service Delivery: AI-first help center (RAG over the policy corpus, see §8), case creation with smart routing, knowledge-base with country/population-aware content targeting, SLA tracking, and satisfaction measurement. Case deflection rate is a first-class product metric.
- **ESS-3 (P1):** Accessibility and localization: WCAG 2.2 AA across all surfaces; UI localization for all operating languages (tier-1 launch set covering ≥ 95% of workforce); all notifications (email, push, SMS) localized and preference-managed.

---
## 5. Workforce Analytics & Reporting (ANLT)

- **ANLT-1 (P0):** Operational reporting: a governed report catalog replacing in-scope PeopleSoft queries/nVision reports (inventory and rationalization is a migration workstream — expect 60–80% of legacy reports to be retired, not rebuilt). Self-service report builder with row-level security inherited automatically from RBAC — a report can never reveal data its runner couldn't see in the UI.
- **ANLT-2 (P1):** Executive analytics: headcount and movement (hires, exits, transfers) with trend and plan-vs-actual, turnover/retention with regrettable-attrition tagging, span-of-control and org-shape analytics, labor-cost analytics fed by Payroll Hub employer-cost data, DEI dashboards with small-population suppression rules (no cell below n=5 rendered), and time-to-fill/talent-flow metrics.
- **ANLT-3 (P1):** Data platform: event-streamed replication from operational stores into a governed lakehouse (see §9); semantic layer exposing certified metrics ("headcount" has exactly one definition enterprise-wide); BI-tool connectivity (Tableau/Power BI) under passthrough security.
- **ANLT-4 (P2):** Predictive analytics: attrition-risk scoring with explainability and strict access controls (aggregate views only for most roles), absence-pattern anomaly detection, and workforce-planning scenario modeling (cost of reorg/hiring-plan simulations).

---

## 6. Workflow, Rules & Extensibility Platform (PLAT)

The anti-customization strategy. PeopleSoft estates rot because logic lives in PeopleCode forks; Meridian's equivalent power must live in governed configuration.

- **PLAT-1 (P0):** Workflow designer: visual, versioned approval-flow builder with conditions on any data attribute, hierarchical routing (n-levels-up, role-based, amount-thresholded), parallel/serial steps, SLAs with escalation, delegation rules, and full simulation/test mode against production-shaped data.
- **PLAT-2 (P0):** Business rules engine: shared rule infrastructure used by Time & Labor, Benefits eligibility, validation gates, and notifications — versioned, effective-dated, environment-promotable (dev → test → prod with diff review), and unit-testable with rule-coverage reporting.
- **PLAT-3 (P0):** Configuration lifecycle management: all configuration (org structures excepted) is exportable/importable as reviewable artifacts; environment comparison tooling; change-request linkage for SOX-relevant config changes.
- **PLAT-4 (P1):** Document generation: templated letters/contracts (offer, promotion, employment verification) with per-country template variants, merge fields from any entity, e-signature routing, and automatic filing to the employee document record with retention rules.
- **PLAT-5 (P1):** Notification framework: event-driven, template-managed, multi-channel (email, mobile push, SMS, MS Teams/Slack), per-user preferences, digest options, and localization.

---

## 7. Integration Architecture (INT)

- **INT-1 (P0):** API platform: REST (OpenAPI 3.1) and GraphQL over the canonical domain model; OAuth 2.1/OIDC with fine-grained scopes mirroring RBAC; cursor-based pagination, field-level filtering, and effective-date query parameters on all person/job endpoints; rate limiting with partner tiers; sandbox tenant with synthetic data for partner development.
- **INT-2 (P0):** Event streaming: every domain change published as a versioned event (CloudEvents envelope) on Kafka topics — `worker.hired`, `worker.terminated`, `job.changed`, `absence.approved`, `paycycle.closed`, etc. Consumers include IdP provisioning, ERP, facilities/badging, and the analytics lakehouse. Guaranteed ordering per worker; replay support for consumer recovery.
- **INT-3 (P0):** Identity integration: SCIM 2.0 outbound provisioning to Entra ID/Okta (Meridian is the source of truth for joiner/mover/leaver identity events); SSO via SAML/OIDC for all user access; same-day deprovisioning on termination (target: ≤ 15 minutes from termination effective time).
- **INT-4 (P0):** ERP/Finance: GL journal posting (PAY-6), cost-center master sync (inbound), project master sync for time charging, and headcount-budget reconciliation feeds.
- **INT-5 (P1):** Standard connector catalog: background-check vendors, e-signature, assessment providers, LMS content providers, equity platforms, benefits carriers (EDI 834), occupational-health, and works-council data interfaces — all built on the adapter framework with per-connector monitoring dashboards.
- **INT-6 (P0):** Integration observability: every interface (API, event, file) has health dashboards, failure alerting, message-level tracing with correlation IDs end-to-end (a payroll input is traceable from UI keystroke to provider file line), and replay tooling.

---

## 8. AI-Native Capability Layer (AI)

AI is a platform layer with centralized governance, not per-module bolt-ons.

### 8.1 Architecture

- **AI-1 (P0):** Central AI gateway: all model calls route through one gateway providing model abstraction (Claude family primary; provider-pluggable), prompt/version management, per-use-case cost and latency budgets, PII redaction filters, full request/response logging to the AI audit store, and tenant data isolation (no training on enterprise data; zero-retention agreements with model providers).
- **AI-2 (P0):** Knowledge retrieval service over the HR corpus — policies, handbooks (per country/population variants), collective-bargaining agreements, benefits plan documents, and process guides. Given the corpus profile (structured, modestly sized, frequently regenerated on policy updates, and requiring strict variant safety so a Germany employee never receives US policy answers), retrieval uses a **hierarchical index-tree / vectorless-RAG approach with population-scoped routing** as the primary strategy, with embedding search as a secondary recall path. Every answer carries citations to the governing document version and an as-of date.
- **AI-3 (P0):** Agent framework: LangGraph-based orchestration for multi-step agents with typed tool contracts into Meridian APIs, mandatory human-approval gates on any state-changing action involving money, employment status, or access rights, step-level audit capture, and kill-switch per agent.

### 8.2 Employee-facing AI

- **AI-4 (P0):** HR Copilot in ESS: conversational answers grounded in the employee's own context (their country, plan enrollments, balances) plus the policy corpus — "How much parental leave do I get?" answers from *their* country policy and *their* tenure. Executes transactions conversationally with confirmation screens ("Request next Friday off" → drafted PTO request → employee confirms). Target: ≥ 30% HR case deflection.
- **AI-5 (P1):** Benefits decision support during enrollment: plan-comparison explanations and scenario modeling ("with two planned dependents and these prescriptions, compare total annual cost"), with clear non-advice framing and human-broker escalation.

### 8.3 Manager & HR-facing AI

- **AI-6 (P1):** Manager Copilot: drafts job descriptions from the job catalog, summarizes a team's cycle status, explains policy in manager terms ("what are my obligations when someone requests FMLA?"), and pre-fills transaction forms from natural-language intent — always landing on a reviewable form, never direct commit.
- **AI-7 (P1):** HR case assist: suggested responses grounded in knowledge base, case summarization, sentiment/urgency triage, and similar-case retrieval.
- **AI-8 (P1):** Recruiting assist: JD drafting with bias-language linting, resume-to-requisition relevance explanation (rank-and-explain, never auto-reject), interview-question generation from competencies, and structured-feedback summarization.

### 8.4 Operations AI

- **AI-9 (P0):** Payroll anomaly detection: per-record scoring on every pre-payroll validation run (variance vs. history, peer-group outliers, suspicious bank-change patterns), with explainable flags into the PAY-3 review queue. This runs from the first parallel cycle — it is also a migration-quality weapon.
- **AI-10 (P2):** Data-quality agent: continuously scans for inconsistencies (manager loops, orphaned positions, stale work permits, address/tax-locale mismatches) and opens remediation tasks with suggested fixes.

### 8.5 AI Governance (P0, non-negotiable)

- Use-case registry with risk classification per the **EU AI Act** (employment-related AI is high-risk: conformity obligations, human oversight, logging) and **NYC Local Law 144** (bias audits for automated employment decision tools), plus emerging state laws (Colorado AI Act).
- Mandatory human decision-making for hiring, promotion, compensation, discipline, and termination — AI informs, humans decide, and the system records who decided.
- Quarterly adverse-impact testing on any AI feature touching candidate or employee evaluation; published model cards internally; works-council consultation artifacts for EU deployments.
- Employee transparency: visible "AI-generated" attribution on all AI-drafted content; opt-out paths where legally required.

---

## 9. Technical Architecture (TECH)

### 9.1 Platform

- **TECH-1:** Cloud-native on a primary hyperscaler (AWS reference architecture; Azure as the documented alternative), Kubernetes (EKS) with GitOps deployment (ArgoCD), infrastructure-as-code (Terraform), and multi-AZ by default.
- **TECH-2:** Service decomposition by bounded context: Person, Organization, Employment, Time, Absence, Payroll Hub, Benefits, Compensation, Talent (Recruiting/Performance/Learning/Succession), Service Delivery, Workflow, Notification, AI Gateway, Analytics. Services own their schemas; cross-domain reads go through APIs or the event-sourced read models — no shared-database coupling.
- **TECH-3:** Data stores: **PostgreSQL** as the system-of-record database per service (partitioned for the 50K+ scale with full history — expect 100M+ effective-dated rows in employment history alone), Kafka for the event backbone, Redis for caching/sessions, OpenSearch for directory/global search, S3 + Iceberg lakehouse for analytics, and object storage with WORM/object-lock for immutable artifacts (payslips, audit exports).
- **TECH-4:** Temporal data as a first-class platform service: a shared library/pattern implementing effective dating, sequence numbers, and as-of querying consistently across all services — this is the single most PeopleSoft-differentiating technical requirement and must not be reinvented per team.

### 9.2 Non-functional requirements

| Dimension | Requirement |
|---|---|
| Availability | 99.95% for ESS/MSS and APIs; 99.99% for the payroll orchestration pipeline during cycle windows |
| Performance | P95 page interaction < 800 ms; P95 API read < 300 ms; org chart render for 50K nodes via progressive load < 2 s |
| Scale | 50K employees v1; architecture validated to 250K (acquisition headroom); 25K concurrent ESS sessions (payday + open-enrollment peak); pre-payroll validation of 50K records < 10 min |
| RPO / RTO | RPO ≤ 5 min, RTO ≤ 1 hr (tier-1 services); cross-region DR with semi-annual game-day failover tests |
| Batch windows | No nightly-batch dependency for core function (event-driven); heavy jobs (mass transactions, accrual sweeps) horizontally scalable and resumable |

### 9.3 Security

- **TECH-5 (P0):** Hybrid RBAC + ABAC authorization: roles define capability; attribute policies define data scope (org subtree, country, population, sensitivity tier). Field-level sensitivity tiers (e.g., compensation, national IDs, health-related absence reasons, succession data) enforced at the API layer so every consumer — UI, reports, integrations, AI gateway — inherits identical policy. Row-level security in analytics derives from the same policy source.
- **TECH-6 (P0):** Audit: immutable, append-only audit log (write-once storage) of every data modification (who/what/when/before/after/source-channel) **and read-access logging for high-sensitivity data** (compensation views, succession slates, national-ID reveals). Tamper-evidence via hash chaining; 7-year minimum retention with legal-hold override.
- **TECH-7 (P0):** Encryption: TLS 1.3 in transit; AES-256 at rest; field-level envelope encryption for national IDs and bank details with KMS-managed keys and key-rotation; secrets in a managed vault; no production data in lower environments — masked/synthetic data generation pipeline instead.
- **TECH-8 (P0):** Compliance posture: SOC 2 Type II controls from day one, SOX ITGC scope (payroll-feeding systems are in scope), penetration testing each release cycle plus annual third-party test, and a dedicated audit-evidence export workspace for internal/external auditors.

### 9.4 Privacy & data residency

- **TECH-9 (P0):** GDPR/global privacy: lawful-basis register per data category, purpose-limitation enforcement, data-subject rights tooling (access export, rectification, erasure with statutory-retention carve-outs — payroll records can't be erased; they're retained per country statute and the conflict is resolved per-category), and DPIA artifacts maintained per feature.
- **TECH-10 (P0):** Residency architecture: regional data planes where legally required (EU plane for EU workers at minimum; assess India DPDP Act and China PIPL — China likely warrants a separate deployment decision), with a global directory layer holding only minimal routing attributes. Cross-border transfer mechanics (SCCs) documented per flow.
- **TECH-11 (P1):** Retention engine: per-country, per-record-category retention schedules with automated anonymization/purge jobs and certificate-of-destruction logging.

---

## 10. Migration & Parallel-Run Program (MIG)

The product's hardest deliverable. Treated as a product capability, not a one-time project script.

### 10.1 Migration tooling (build once, run hundreds of times)

- **MIG-1 (P0):** Extraction adapters for PeopleSoft (PS_JOB, PS_PERSON, PS_COMPENSATION, position data, accrual balances, benefits elections, performance history, document attachments), preserving **full effective-dated history** — not just current state. History depth decision per domain (recommendation: full job/comp history; 7 years payroll results as queryable archive; performance 5 years).
- **MIG-2 (P0):** Transform/validate pipeline with field-level mapping specs under version control, automated data-quality scoring per domain (completeness, validity, referential integrity), exception queues for data stewards, and idempotent re-runs (the pipeline will execute weekly for months).
- **MIG-3 (P0):** Reconciliation workbench: record counts, field-match rates, and domain-specific checks (accrual-balance recompute match, net-pay history spot recompute) with trend dashboards per country. Gate: ≥ 99.95% field-match on critical fields before a population enters parallel run.

### 10.2 Parallel-run design (6–12 months)

- **Phase A — Shadow (months 1–3):** PeopleSoft authoritative. Nightly CDC sync PeopleSoft → Meridian. Meridian generates payroll inputs per cycle; reconciliation engine compares Meridian-orchestrated provider results against PeopleSoft payroll at pay-element level. No employees see Meridian.
- **Phase B — Pilot dual-entry (months 3–6):** Selected pilot populations (recommendation: one mid-size, lower-complexity country + one US business unit) transact in Meridian with reverse-sync to PeopleSoft. ESS/MSS opens to pilots. Exit per population: three consecutive penny-perfect cycles, < 0.5% transaction error rate, pilot CSAT ≥ 4/5.
- **Phase C — Wave cutover (months 6–12):** Country/region waves become Meridian-authoritative; PeopleSoft moves to read-only for cut-over populations. Wave sequencing by payroll-complexity score and provider readiness. Every wave has a rehearsed go/no-go checklist and a tested 72-hour rollback plan (PeopleSoft re-activation runbook) until wave +2 cycles complete.
- **Phase D — Decommission (months 12–18):** PeopleSoft archived to a queryable read-only store (statutory access obligations), licenses terminated, infrastructure retired.

- **MIG-4 (P0):** Bidirectional sync service with conflict detection, field-ownership matrix per phase, and sync-lag monitoring (alert > 15 min) — the single highest-risk technical component of the program; staffed and tested accordingly.
- **MIG-5 (P1):** Change management as product scope: in-app guided tours, role-based training paths in LEARN, readiness dashboards per wave, hypercare command center with live error feeds, and a feedback channel triaged into the product backlog. Works-council/union consultation completed per country **before** that country's pilot, not before cutover.

---

## 11. Delivery Roadmap

| Phase | Window | Delivery focus |
|---|---|---|
| **Foundation** | Months 0–6 | Platform (TECH), identity, RBAC/ABAC, audit, Core HR P0, temporal-data service, migration pipeline v1, AI gateway + knowledge service |
| **Operational core** | Months 4–10 | Time & Labor, Absence, Payroll Hub + first two provider adapters, Benefits P0, ESS/MSS P0, HR Copilot, compliance training engine |
| **Shadow start** | Month ~8 | Phase A parallel run begins for wave-1 countries |
| **Talent suite** | Months 8–14 | Recruiting, Performance, Compensation cycles, Learning, Succession, analytics P1 |
| **Pilot & waves** | Months 10–20 | Phase B pilots → Phase C wave cutovers |
| **Decommission** | Months 20–26 | PeopleSoft archive and retirement; P2 backlog (predictive analytics, career pathing, market benchmarking) |

Team shape (indicative): 8–10 product squads aligned to bounded contexts, a platform/SRE group, a dedicated migration squad, a country-pack/compliance content team (this is chronically understaffed in failed programs — it is not optional), and an AI governance function. Total ~120–160 engineering/product FTE at peak plus payroll/HR SME secondments per country.

---

## 12. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Payroll-provider data-contract gaps discovered late | High | Critical | Contract-first adapter development; provider conformance test suites; two providers integrated before shadow phase |
| Effective-dated history migration corrupts downstream calc (accruals, seniority) | Medium | Critical | Recompute-and-compare validation (MIG-3); domain stewards sign off per wave |
| Country compliance-pack scope underestimated | High | High | Dedicated country-pack team; legal review per country gate; wave sequencing defers hardest countries |
| Bidirectional sync conflicts during Phase B | Medium | High | Strict field-ownership matrix; conflict dashboards; pilot scale kept small |
| AI features trigger works-council objection or regulatory finding | Medium | High | §8.5 governance executed before deployment per jurisdiction; AI features regionally feature-flagged |
| Scope creep recreating PeopleSoft customizations 1:1 | High | High | "Configuration-only" guardrail; customization-rationalization review board; adopt-not-adapt default |
| Dual-run fatigue (payroll teams running two systems for a year) | High | Medium | Reconciliation automation (not manual ticking); backfill staffing budgeted; wave pacing reviewed quarterly |
| Key-person dependency on PeopleSoft SMEs during migration | Medium | High | Knowledge-capture sprints early; retention incentives; documented extract logic |

---

## 13. Open Questions (require decisions before Foundation phase exit)

1. **Expense management:** native module in Meridian ESS or deep-link to the ERP expense tool? (Recommendation: integrate, don't build — expenses are ERP-domain.)
2. **Provider portfolio:** which payroll providers per country/region? Drives adapter sequencing; RFP needed in month 0–2.
3. **China and Russia-adjacent jurisdictions:** in scope for the global tenant or separate deployments per residency law?
4. **Performance philosophy:** ratings vs. ratingless, forced distribution — HR leadership decision that shapes PERF configuration defaults.
5. **History depth:** confirm per-domain migration history retention (proposed in MIG-1).
6. **Union/works-council inventory:** complete register of consultation obligations and timelines per country — gating item for wave planning.
7. **Build vs. buy at the edges:** ATS and LMS have strong SaaS markets; confirm the strategic intent to build natively for suite coherence vs. integrating best-of-breed for the talent edge modules.

---

## Appendix A — Canonical Domain Model (summary)

Core aggregates: **Person** (identity, demographics, IDs, contacts) → **Worker** (one per employment relationship; supports multi-job) → **Assignment** (effective-dated job/position/comp/manager state) → **Position** → **Job Profile** → **Organization** (legal entity / BU / department trees) → **Compensation Record** → **Absence/Time Results** → **Pay Cycle / Pay Result** (hub-ingested) → **Enrollment** (benefits) → **Talent artifacts** (goals, reviews, applications, learning records, succession slates). All aggregates: effective-dated, audit-chained, event-published.

## Appendix B — PeopleSoft Parity Map (to be completed during discovery)

A traceability matrix mapping every PeopleSoft component/page/process in current production use (from usage telemetry and the customization inventory) to its Meridian requirement ID or an explicit retirement decision. No PeopleSoft capability may be undocumented at parallel-run start — "we forgot that page existed" is the classic source of cutover-week emergencies.

---
*End of document.*

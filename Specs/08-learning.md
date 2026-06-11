# Deep-Dive PRD 08 — Learning & Development (LMS)
*Project Meridian | Depends on: 01-Core (population rules, job profiles), 12-Platform | Feeds: 09-Succession (skills), compliance posture*

## 1. Mission & Success Metrics
Zero-lapse compliance training across 30+ jurisdictions, plus a modern learning experience that builds the skills the org plans around.
- Compliance completion: ≥ 99% by due date, 100% within grace; lapse-caused regulatory findings: 0.
- Assignment-to-availability latency: rules evaluate new hires/role changes < 1 h.
- Learner satisfaction ≥ 4.3/5; content launch success rate ≥ 99.5% (SCORM/xAPI runtime reliability).

## 2. Catalog & Content
- Item types: e-learning (SCORM 1.2/2004 player with suspend/resume, xAPI with LRS), instructor-led (sessions: capacity, waitlist with auto-promote, location/VC, instructor assignment + qualification check, attendance capture incl. QR/mobile), blended curricula (ordered/unordered sets with equivalency rules), external content (LinkedIn Learning/Coursera/Udemy adapters: catalog sync + completion ingestion), documents/videos with completion tracking, assessments (question banks, randomization, pass thresholds, attempt limits, proctoring flag P2).
- Versioning: content version supersedes with policy (in-progress learners finish old vs. restart); completion records pin content version (audit answer to "which version did they take in 2027").
- Equivalencies: external cert or prior completion satisfies requirement (mapping table + evidence upload + approver).

## 3. Compliance Engine (P0 — live before any country pilot)
- Requirement objects: regulation reference, population rule (role/job profile hazard flags/location/legal entity/manager-status), initial deadline (days from trigger event), recurrence (fixed-date vs. rolling anniversary), grace period, escalation ladder (worker → manager → HR → compliance officer at T-14/T-7/overdue), consequence hooks (system-access flag, assignment-block event for safety-critical roles — policy-gated).
- Jurisdiction packs: US state harassment-prevention matrices (CA SB1343 2-hr supervisor/1-hr nonsupervisor biennial, NY annual, IL annual, CT…), OSHA-driven safety (role-based: lockout/tagout, HazCom), industry add-ons configurable; packs versioned with regulatory-change notes (shared model with Core country packs).
- Dashboards: compliance officer (population coverage, due/overdue heatmaps, audit export with evidence: completion timestamp, content version, score, attestation), manager team view, worker "my requirements" with one-click launch.
- **Acceptance:** new regulation pack deployable as configuration in < 5 days; population re-evaluation after org change < 1 h; audit evidence export for any worker < 30 s.

## 4. Learner & Manager Experience
Personal learning home: required (deadline-sorted), recommended (AI, see §6), in-progress resume, history/transcript (print/PDF for external use). Search with skill tagging. Manager: assign with due date, team transcript, approve-request flow for paid/external content with budget pools. Mobile: full launch capability, offline download for video content (P1.5).

## 5. Certifications, Licenses, Tuition
External certification registry: type catalog (issuer, validity period), worker records with evidence docs, expiry pipeline (90/60/30 alerts to worker+manager), job-requirement linkage (job profile requires cert X ⇒ incumbent lapse raises Core compliance flag + optional assignment block). Tuition reimbursement (P2): application (program, cost, policy cap check), approval, grade-evidence gate, reimbursement → CPDC element with taxability ($5,250 US exclusion logic metadata), clawback agreement tracking on exit (offboarding checklist hook).

## 6. AI & Skills (P1.5–P2)
Skills graph: taxonomy (build on open frameworks + custom), inference from job history/completions/project data with worker confirm/decline (self-sovereign profile), gap analysis vs. current role and target role (09-Succession career paths); recommendation engine (gap-driven + cohort patterns) with explanation; content Q&A copilot over enrolled course materials (licensed-content boundary respected); auto-draft course descriptions/quiz items for L&D authors (human-published only).

## 7. Events & APIs
Events: assignment.created, completion.recorded, requirement.overdue, certification.expiring. APIs: transcript API, completion webhook for external platforms, requirement-status API (Core/REC gating checks: interviewer-certified, safety-qualified for shift claim in 02-TIME).

## 8. Edge Cases Register
Leave during compliance window (clock pause per policy/country); content vendor outage during deadline week (deadline-extension batch tool + evidence note); SCORM suspend-data corruption (resume fallback + attempt protection); acquired-population historical transcript import (16-Migration: minimum = compliance-relevant history); contractor training scope (lightweight worker records).

## 9. Open Questions
LMS build-vs-buy confirmation (master §13.7; this assumes build — compliance engine is the differentiator; commodity content delivery could be partnered). LRS retention policy and analytics scope.

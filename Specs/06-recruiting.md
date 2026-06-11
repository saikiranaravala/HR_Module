# Deep-Dive PRD 06 — Recruiting & Onboarding (ATS)
*Project Meridian | Depends on: 01-Core (positions), 12-Platform | Feeds: 01-Core hire, 08-Learning (day-1 training)*

## 1. Mission & Success Metrics
Position-driven, compliant, candidate-respectful hiring at enterprise scale — with zero re-keying between offer and employee record.
- Time-to-fill: −20% vs. baseline within 12 months; offer-to-hire data re-entry: 0 fields.
- Candidate NPS ≥ +40; application completion ≥ 80% started→submitted.
- Adverse-impact monitoring live on 100% of pipelines (LL144/EU AI Act readiness).

## 2. Requisition Lifecycle
Create from vacant position (inherits job profile, grade, location, budget — budget check against position comp budget with Finance-exception path) or evergreen/pipeline req type → approval matrix (headcount type: backfill auto-approves lighter than net-new) → posting composer (AI-drafted from job profile, bias-language lint, salary-range disclosure auto-injected per jurisdiction law: CO/CA/NY/WA + EU directive) → channel distribution (career site, internal-first window policy, Indeed/LinkedIn feeds, agency portal with ownership/duplicate rules + fee tracking) → status board (open/hold/filled/cancelled with aging alerts).

## 3. Candidate Experience
- Career site: CMS-lite branding, search with geo/remote filters, job-alert subscriptions, WCAG 2.2 AA, ≤ 5-min apply (resume parse → prefill → confirm; mobile resume-less apply option), status transparency in candidate portal, communication preference center.
- Privacy: per-jurisdiction consent capture, retention clocks (auto-purge per country: e.g., 6-month default EU with re-consent campaigns), DSAR support, talent-pool opt-in distinct from application.
- Internal candidates: separate experience (no resume re-upload; profile-based), confidential-application policy toggle (manager notification rules per policy decision), internal-mobility SLA commitments surfaced.

## 4. Pipeline & Selection
- Configurable stage flows per req template (new → screen → interview loop(s) → offer) with stage SLAs, bulk actions, disposition reason taxonomy (OFCCP-compliant codes, mandatory at rejection).
- **AI screening (rank-and-explain only):** relevance score vs. requisition with cited evidence (skills/experience matches), never auto-reject, recruiter sees and can ignore; knockout questions (objective only: work authorization, license) are deterministic rules, not AI. Bias audit hooks: stage pass-through by protected class (where lawfully inferable/collected) monitored quarterly; NYC LL144 annual independent audit artifact support.
- Interview management: kits per stage (competency-based question banks from job profile, structured scorecards with anchored scales), panel scheduling (calendar free-busy, room/VC booking, candidate self-schedule links with timezone handling), interviewer load balancing + training-status check (interviewer certification from 08-LEARN), feedback SLA nudges, debrief mode (scores hidden until own submission to prevent anchoring).
- Assessments/background: vendor adapters (HackerRank/SHL; Sterling/HireRight for background with per-country package mapping, adjudication workflow with individualized-assessment support per EEOC guidance, FCRA pre-adverse/adverse letter automation).

## 5. Offer → Hire
Offer builder: country template + comp validation against range (out-of-range routes to comp team), sign-on/equity/relocation components with clawback terms recorded, approval chain, e-signature, expiry/reminder automation, negotiation versioning (full history). On accept: pre-hire record → 01-Core hire flow with background-clear gating, start-date change propagation (one change updates onboarding tasks, payroll expectations, IT provisioning), declined-offer reason capture → analytics.
**Acceptance:** offer accept → onboarding portal live for candidate < 15 min, zero recruiter re-entry.

## 6. Onboarding (pre-day-1 through day 90)
Pre-boarding portal: welcome content per org/country, document collection (e-sign policies, statutory forms launched: I-9 section 1, W-4 wizard, country equivalents), team intro, equipment preference. Task orchestration to stakeholders (manager checklist, IT via ITSM ticket adapter, facilities). Day-1 automation: IdP activation, badge, LEARN day-1 compliance assignments, buddy assignment. 30/60/90 check-in scheduling into 07-PERF check-ins; onboarding survey at 30/90 → analytics. New-hire failure-to-start handling (offer rescind/no-show flow reverting position to open).

## 7. Compliance & Reporting
OFCCP: applicant-flow logs, internet-applicant rule data capture, disposition completeness enforcement. EEO/diversity voluntary self-ID (separated storage, recruiter-blind). Posting compliance registry per jurisdiction (pay transparency text blocks). Agency contract/fee audit trail. Req-to-hire full audit chain.

## 8. Events & APIs
Events: requisition.opened/filled, application.stage.changed, offer.extended/accepted/declined, hire.completed. APIs: public careers API (postings), partner APIs (assessment/background callbacks), internal: POST /hires (Core handoff contract — the most tested interface in the suite).

## 9. Edge Cases Register
Candidate is a rehire with do-not-rehire flag (policy-gated visibility to recruiter); internal candidate rejected (sensitive notification handling + manager data wall); offer accepted then counter-offer rescind flow; multi-req single candidate (shared profile, per-req dispositions); requisition cancelled with offers out; background adverse finding post-start (escalation runbook); GDPR erasure request mid-pipeline.

## 10. Open Questions
Build-vs-buy final confirmation for ATS (master PRD §13.7): this PRD assumes build; if buy (Greenhouse/SmartRecruiters), it becomes an integration spec — decision gates Talent-suite phase. CRM/sourcing (talent marketing) scope: P2 or partner.

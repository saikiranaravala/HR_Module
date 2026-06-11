# Deep-Dive PRD 10 — Employee & Manager Self-Service + HR Service Delivery
*Project Meridian | Depends on: all modules (this is the front door) | Owns: mobile apps, help center, case management*

## 1. Mission & Success Metrics
Consumer-grade front end where 50K employees and 6K managers complete HR tasks in seconds — and an AI-first help layer that deflects a third of case volume.
- Adoption: ≥ 85% MAU within 90 days of each wave cutover; mobile share ≥ 50%.
- Task completion: top-10 ESS tasks median < 60 s; MSS approval median < 30 s from notification tap.
- Case deflection ≥ 30%; case SLA attainment ≥ 95%; CSAT ≥ 4.4/5.

## 2. Experience Architecture
- Surfaces: responsive web app + native iOS/Android (shared design system; native for push, biometric auth, offline payslips, punch geofencing). SSO + device biometric step-up for sensitive actions (bank change, tax forms).
- Home: personalized card feed (pending tasks, payday countdown with net amount once published, balance snapshot, enrollment windows, recognition), global search (people directory, policies, tasks — security-trimmed), notification center with channel preferences.
- Personalization rules: cards target by country/population/lifecycle moment (new-hire mode for first 90 days; pre-retirement content); localization: full UI in tier-1 languages (≥95% workforce coverage), content fallback chains.
- Accessibility: WCAG 2.2 AA audited per release; screen-reader test suite in CI.

## 3. Employee Self-Service (task specs)
- **Payslips:** list + detail with plain-language element glossary (tap any line → explanation), YTD views, PDF download, year-end docs vault; "explain my payslip change" AI action (diff vs. last cycle, grounded in elements — e.g., "net lower because benefits OE elections started").
- **Pay setup:** direct deposit management (add/edit/split; verification via instant micro-deposit partner or penny-test; fraud interlocks: change freeze window before payday + out-of-band confirmation; alerts on change to all registered channels), tax withholding wizards (US federal W-4 guided flow with IRS-aligned steps, state forms by work/residence locale; country equivalents) routing to PAY hub.
- **Time & absence:** punch widget (geofenced), timesheet entry, PTO request with balance projection + team-calendar conflict hint, request status tracking.
- **Personal data:** name/address/contact/emergency/dependents with country-specific validation, doc-evidence steps where statutory (name change), pending-approval visibility.
- **Benefits:** enrollment flows (04), current elections summary card, life-event launcher, total-rewards statement.
- **Documents:** e-sign inbox, employment-verification self-service letter generation (templated, QR-verifiable) + The Work Number-style integration option, personal document vault.
- **Directory & org:** people search, org chart, profile pages (worker-controlled extras: pronouns, skills, about).
- **Expenses:** deep-link integration to ERP expense tool (per master §13.1 recommendation) with SSO context handoff.

## 4. Manager Self-Service
- **Unified approval inbox:** all types (time, absence, job changes, comp, requisitions, learning requests) in one queue with type filters, bulk approve with guardrails (no bulk on comp), delegation (vacation rules with scope + duration limits, audit), out-of-office auto-route; full context cards (approving a raise shows compa-ratio, budget impact, guideline position — decision-quality at the point of approval).
- **Team hub:** roster with status glances (on leave, anniversary, new), absence heat-map calendar, time-compliance widget (missing timesheets one-tap nudge), performance-cycle progress, headcount vs. budget, recent changes feed.
- **Transactions:** initiate transfer/promotion/comp change/termination via guided flows (rendered from 12-Platform workflow definitions — zero per-transaction custom UI), with eligibility pre-checks and draft-save.
- **Team analytics lite:** turnover, tenure mix, span — scoped to hierarchy, suppression rules under n=5.

## 5. HR Service Delivery (case + knowledge)
- **AI-first help (the front line):** copilot answers from policy corpus (14-AI: population-scoped retrieval — country/union/grade variants enforced at retrieval), personal-context grounding (their balances/elections), citations + as-of dates, confidence-gated: low confidence → seamless case-creation handoff with conversation transcript attached (no repetition for the employee).
- **Case management:** smart routing (topic classification → queue: payroll, benefits, ER…), priority/SLA matrices, employee-relations cases in segregated security tier (separate queue, restricted visibility, investigation workspace with evidence vault and privilege flags — whistleblower-directive separation honored), case timeline with internal vs. employee-visible notes, knowledge-suggested responses for agents, satisfaction survey on close.
- **Knowledge base:** structured articles with population targeting metadata (the same variant-safety model as retrieval), versioning + review cycles (stale-content alerts at 12 months), authoring workflow with legal-review gate for policy articles, analytics (search-with-no-result mining → content backlog).
- **Acceptance:** copilot answer P95 < 6 s; deflection measured honestly (answered-and-no-case-within-72h on same topic).

## 6. Notifications Framework Usage
Event-driven catalog (~80 notification types at launch) with per-type channel defaults + user overrides, digest mode, quiet hours by timezone, mandatory-channel exceptions (legal notices ignore preferences), localization per recipient.

## 7. Edge Cases Register
Terminated worker access: payslip/tax-doc portal access post-exit per country retention (limited-scope alumni auth); workers without corporate devices/email (frontline mode: kiosk auth + SMS/personal-email channel with consent); delegated approver attempts self-approval (blocked + logged); manager of manager visibility boundaries in analytics; legal-hold worker data-change freeze messaging.

## 8. Open Questions
Native app release trains vs. wave schedule (app must precede first pilot). Frontline kiosk hardware standard. Alumni portal scope (recommend minimal: docs only).

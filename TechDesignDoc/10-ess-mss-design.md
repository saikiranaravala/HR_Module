# Module 9 Design — ESS/MSS + HR Service Delivery (Specs/10)

**Spec:** [Specs/10-ess-mss.md](../Specs/10-ess-mss.md) · **Package:** `src/ess_mss/` · Tests: `src/test/ess_mss/`
**Depends on:** rules_workflow (approval routing, case-routing decision tables), ai_layer (help copilot via gateway + population-scoped retrieval), platform_core (policy T3 segregation, audit), core_hr / time_labor / payroll_hub / benefits (task targets)

## 1. Scope & Requirement Trace

| Req | Design element | Local scope |
|---|---|---|
| ESS-1 (P0) | ESS *task plumbing* delegates to the owning modules (02 time/PTO, 03 payslips, 04 enrollment); new here: bank-change fraud interlock (freeze window before payday + out-of-band confirm), pending-approval visibility, alumni/legal-hold/frontline access modes | **Yes** (web/native UI surfaces deferred to UI phase — this module is the service layer those surfaces call; W-4 wizards, e-sign, expenses deep-link deferred) |
| MSS-1 (P0) | `inbox.py`: unified approval inbox over `rules_workflow.StepExecution` (type filters, bulk-approve with **no-bulk-on-comp** guardrail), `Delegation` records (scope + duration limits, audited), delegate **self-approval block**; `team.py`: team analytics lite with hierarchy scoping + **n<5 suppression** | **Yes** (team hub cards / heat-maps = UI phase; transaction initiation flows already exist as workflow definitions in 12) |
| ESS-2 (P0) | `help.py`: copilot answer via AI Gateway (population-scoped retrieval, citations, confidence gate → case handoff with transcript); `cases.py`: smart routing (ruleset `case-routing`), SLA matrix, **ER segregated tier (T3)**, internal vs employee-visible notes, CSAT on close, honest deflection metric (no same-topic case within 72 h); `knowledge.py`: articles with population targeting, 12-month stale alerts, legal-review gate for policy articles | **Yes** |
| ESS-3 (P1) | `notifications.py`: catalog config (per-type channel defaults), user overrides, quiet hours by timezone, **mandatory-channel exceptions** (legal notices ignore preferences), frontline SMS/personal-email channel behind consent | **Yes** (localization rendering = UI phase) |

## 2. Data Model (schema `service_delivery`)

| Table | Notes | Tier |
|---|---|---|
| `case` | topic, queue, priority, SLA due, status, worker_id, transcript ref | T1; **queue `er` rows are T3** (restricted visibility, policy-gated, read-audited) |
| `case_note` | `visibility` = internal \| employee | follows case |
| `kb_article` | population targeting (country/union/grade), version, review_due, `requires_legal_review` | T0 content, T1 targeting |
| `delegation` | delegator, delegate, scope (types), start/end, audited create/revoke | T1 |
| `notification_pref` | worker × notification type → channel override, quiet hours, consent flags | T1 |
| `access_grant` | alumni grants: scope (payslip/tax-doc only), expiry per country retention config; legal-hold freeze flags | T1 |

Catalog tags: category `service-delivery`, purpose `hr-service`, lawful basis `legitimate-interest` (ER cases: `legal-obligation`), retention `cases-5y`. No new temporal entities (cases/articles are versioned, not effective-dated) — temporal pattern not required here; audit via `platform_core.audit`.

## 3. Rules & Configuration Surface

- `case-routing` ruleset: topic → queue (payroll, benefits, er, general) + priority/SLA hours. Decision table, versioned, golden cases.
- Notification catalog: YAML config (type → default channels, mandatory flag, digest-eligible).
- Alumni retention windows per country: config map in `ess_mss/config/` (country pack style — no `if country ==` in code).

## 4. AI Touchpoints

- `help-center-copilot` use case via AI Gateway (Haiku-class), population-scoped retrieval from 14's corpus; answers carry citations + as-of date. Confidence below threshold → `create_case_from_conversation` (transcript attached, no re-typing). Draft-only: copilot never mutates data. Risk tier: limited (no money/employment/access mutation).

## 5. Edge-Case Test Plan (register §7)

| Register row | Test |
|---|---|
| Terminated worker portal access (alumni, limited scope, country retention) | `test_ESS_terminated_worker_alumni_scope` |
| Workers without corporate devices (frontline: kiosk + SMS/personal email w/ consent) | `test_ESS_frontline_channel_requires_consent` |
| Delegated approver attempts self-approval | `test_MSS_delegate_self_approval_blocked` |
| Manager-of-manager analytics visibility boundary (n<5 suppression) | `test_MSS_team_analytics_scope_and_suppression` |
| Legal-hold worker data-change freeze messaging | `test_ESS_legal_hold_change_freeze` |

## 6. Key Decisions / Invariant Notes

- **UI surfaces deferred** (per repo convention) — this module is the backend the front door calls; ESS task logic stays in owning modules (no duplication, Invariant #2).
- ER-case segregation rides the **central policy engine** (capability `case:read-er`), not local checks (Invariant #3); ER reads logged via `read_with_audit`.
- Inbox aggregates `StepExecution` rows through `rules_workflow` services — no foreign-schema joins (Invariant #2).
- Copilot routes only through the AI Gateway with the calling user's scope (Invariant #6).
- Events deferred per memory (notification dispatch is a direct call behind an interface an event bus can later replace).

## 7. Open Items

- Expenses: master §13 still open (ERP deep-link recommended by Specs/10 §3) — nothing built locally.
- Native app release trains, kiosk hardware standard, alumni portal scope (Specs/10 §8) — product decisions, not gating local backend.

## Change Log

- **2026-06-11** — Initial design. Trigger: Module 10 kickoff (post-Benefits, auto-approved cadence).
- **2026-06-11** — Review fixes: inbox now surfaces `role:X`-routed steps to role members (`inbox(..., roles=...)`); team-analytics org scoping uses `platform_core.orgpath.within` ('/'-boundary matching); alumni retention uses calendar months (`platform_core.dates.add_months`).

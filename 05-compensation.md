# Deep-Dive PRD 05 — Compensation Planning & Administration
*Project Meridian | Depends on: 01-Core, 07-Performance (ratings), 13-Integration (equity platforms) | Feeds: 03-Payroll Hub*

## 1. Mission & Success Metrics
Administer pay foundations and run global comp cycles that 6,000 managers complete on time with guideline discipline — and surface pay-equity risk before regulators do.
- Cycle completion: 100% worksheets submitted by deadline (escalation automation); cycle admin effort −50% vs. PeopleSoft baseline.
- Budget discipline: ≤ 0.5% variance between allocated and committed spend per cycle.
- Zero comp data leaks: access violations = 0 (most-audited domain).

## 2. Compensation Foundation
- **Structures:** grade ladders per country/job family; ranges (min/mid/max) effective-dated; geographic differentials (zone tables: e.g., US metro zones at 100/95/90% of national); range refresh workflow with mass-update simulation (who falls below new min → remediation list).
- **Pay components catalog:** base (salary/hourly with annualization factors), allowances (car, housing, shift — each with taxability + pensionability metadata per country, recurring schedule), one-time (sign-on with clawback terms tracked, referral, spot awards with budget pools), target bonus % per grade.
- **Derived metrics on every comp record:** compa-ratio, range penetration, position-in-range percentile vs. peers — computed server-side, surfaced under permission tiers.
- **Comp change transaction:** reason taxonomy (merit, promotion, market, equity-adjustment, demotion), guideline display at entry, approval matrix (out-of-range or > X% requires comp-team), effective-date rules (cycle-aligned vs. ad hoc), payroll element generation.

## 3. Cycle Management (annual merit/bonus/equity)
- **Setup:** cycle template (eligibility rules: hire-date cutoffs, status, performance-doc requirement; proration: hire date, LOA days, FTE-change weighted), budget model (top-down pools cascading the supervisory tree with hold-back %, or bottom-up guideline-generated), guideline matrix (performance rating × compa-ratio quartile → recommended % range), currency model (plan local, budget corporate at locked cycle FX), calendar with gates.
- **Manager worksheet:** team grid (current comp, ratings, compa-ratio, last increase, flags), recommendation entry with live budget bar and guideline conformance coloring, out-of-guideline justification (mandatory text + approval flag), proposed-promotion sub-flow (grade change + range validation), what-if total before submit.
- **Roll-up & calibration:** n-level roll-up views, redistribute-down capability, calibration mode (cross-team comparison, adjustment with dual-entry audit: original vs. calibrated), executive approval gates per division.
- **Statementing:** comp statements generated per worker (merit %, new salary, bonus, equity) with manager-delivery workflow and embargo until release date; payroll elements auto-generated at effective date.
- **Acceptance:** worksheet load for 100-report manager < 2 s; full-cycle recalculation (FX or budget change) across 50K < 20 min; mid-cycle org moves handled by snapshot policy (population frozen at cycle start, exceptions admin-managed) — explicit, documented behavior.

## 4. Variable Pay & Equity
- Bonus plans: formula-driven (corporate × unit × individual multipliers with caps/floors), proration engine shared with merit, off-cycle discretionary pools with approval, payout file → CPDC with tax treatment (supplemental rates flag).
- Equity: grant records (options: strike/expiry; RSUs: vest schedule incl. cliff+quarterly; ESPP enrollment data), vesting calendar with event feed → PAY at taxable events (vest FMV ingestion from equity platform), platform integration (Shareworks/Carta/Fidelity adapters: outbound grants + demographics, inbound transactions), blackout/insider lists honored in displays.
- Recognition (P2): peer-to-peer points platform integration or native lightweight awards with taxability routing.

## 5. Market & Pay Equity (P1.5–P2)
- Survey management: import Mercer/Radford/WTW with job-matching workbench (catalog code ↔ survey code mappings, match confidence), market composites per job/geo, aging factors; market-reference dashboards (compa vs. market percentile).
- **Pay-equity workbench:** regression model (controls: grade, tenure, location, performance) with protected-class gap output, statistical significance flags, drill to cohorts, remediation scenario modeling (cost to close gaps under strategies), legal-privilege mode (analyses run under privilege flag with restricted artifacts). Supports **EU Pay Transparency Directive** obligations: gap reporting, salary-range disclosure data for REC postings, worker right-to-information responses (per-request report generation).

## 6. Security Posture (strictest non-health domain)
Field-tier: comp visible only via explicit capability grants; manager sees direct+indirect reports only with dollar values, peers never; comp analysts scoped by division; read-access logging on every comp view (TECH-6); export controls (watermarked, logged, DLP-tagged files); calibration views mask names optionally per policy.

## 7. Events & APIs
Events: comp.changed (typed: merit/promo/adhoc), cycle.opened/submitted/approved/released, equity.vest.upcoming. APIs: GET /workers/{id}/compensation?as_of; cycle worksheet APIs (bulk save with optimistic locking); POST /comp-changes with guideline evaluation response.

## 8. Edge Cases Register
Promotion + merit in same cycle (sequencing & range basis rules); retro merit after termination (final-pay supplement flow); FX swing mid-cycle (rate locked, variance reported); worker below new range min post-refresh (auto-remediation proposal); manager self-recommendation block (skip-level routes own record); dual-currency expats (split comp records with home/host shadow).

## 9. Open Questions
Equity platform of record confirmation (drives adapter). Bonus accrual feed to Finance: monthly estimated accrual model in scope? (Recommend yes, P1.5.) Ratingless-cycle support depth pending 07-PERF philosophy decision.

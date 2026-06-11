# Deep-Dive PRD 04 — Benefits Administration
*Project Meridian | Depends on: 01-Core, 12-Platform rules | Feeds: 03-Payroll Hub (deductions/imputed income), carriers*

## 1. Mission & Success Metrics
Configure any plan, evaluate eligibility continuously, run enrollment flawlessly at 50K scale, and keep carriers penny-accurate.
- Open enrollment: 100% completion (active or default) by deadline; system P95 < 1 s during peak (25K concurrent).
- Carrier discrepancy rate: < 0.2% of enrollment records per file cycle.
- Deduction accuracy: zero benefits-caused payroll variances post-stabilization.

## 2. Plan Configuration Model
- **Hierarchy:** Program → Plan Type (medical, dental, life, STD/LTD, retirement, FSA/HSA, voluntary) → Plan → Option (coverage tier: EE, EE+Spouse, EE+Family…) → Rate.
- **Rates:** effective-dated tables; dimensions: age (with age-determination rule: as-of Jan 1 vs. birthday), salary band/multiple (life: 1–5× with rounding + guaranteed-issue caps + EOI thresholds), tobacco status, region. Employer/employee split by % or fixed; pre/post-tax treatment metadata per country.
- **Retirement:** 401(k)/Roth with match formulas (tiered: 100% of first 3% + 50% of next 2%), true-up flag, annual limits sync (402(g)/415 catch-up by age), auto-enrollment + auto-escalation rules; UK auto-enrolment (qualifying earnings bands, postponement, re-enrolment triennial); IN PF/EPS statutory data capture; DB pension data interface (admin stays with pension provider).
- **Plan-year versioning:** clone-and-amend tooling for annual setup; side-by-side config diff; effective Jan-1 (or per-country year) with mid-year amendment audit.

## 3. Eligibility Engine
- Rule dimensions: worker type, FTE threshold, location/country, union, grade, waiting period (first-of-month-after-30-days style date math library), ACA full-time determination (look-back measurement: configurable measurement/admin/stability periods, variable-hour tracking from TIME data, break-in-service rules).
- **Continuous evaluation:** subscribes to Core events (hire, FTE change, location change, leave, termination); eligibility delta → event generation (gain ⇒ enrollment opportunity with window; loss ⇒ termination of coverage + continuation event).
- **Acceptance:** full-population re-evaluation (50K) < 30 min; event-driven single-worker evaluation < 5 s.

## 4. Enrollment Experiences
- **New hire:** window per plan (e.g., 30 days), guided flow, default plans on window expiry per policy, retro deduction handling (catch-up calc to PAY).
- **Life events:** catalog (marriage, birth/adoption, divorce, dependent aging-out with auto-detection at 26/country age, spouse coverage loss…) with per-event allowed-change matrix (IRS Section 125 consistency rules), documentation requirements + verification queue, 30/60-day windows.
- **Open enrollment:** wave capability (stagger by region), in-progress save, side-by-side comparison with personalized cost (per-paycheck framing), AI decision support (see 14-AI; non-advisory framing, logged), dependent re-verification campaigns, EOI routing to carriers with pending-coverage state, confirmation statements (PDF + ESS), post-close correction window with admin audit.
- **Defaulting policy:** per plan type (carry-forward vs. waive) — configuration, with simulation of default outcomes before OE opens.

## 5. Carrier & Vendor Connectivity
- Outbound: EDI 834 (full + change files per carrier preference), proprietary formats via adapter framework (shared with 03-Hub pattern), per-carrier calendars, file-level acks + member-level error ingestion → discrepancy workbench with retransmit.
- Retirement provider: payroll-deduction/contribution files per cycle, loan-repayment ingestion → PAY deduction elements, limit-reached feedback loop.
- FSA/HSA administrator feeds; COBRA administrator event file (qualifying events with coverage snapshot).
- **Audit:** quarterly carrier census reconciliation tooling (carrier roster import → diff vs. Meridian → workqueue).

## 6. Payroll Interlock
Deduction derivation per cycle: active enrollments × rates × per-period conversion (semi-monthly vs. biweekly 24/26 logic, 3-paycheck-month suppression rules) → CPDC BenefitDeductions; arrears engine for unpaid-leave gaps (catch-up schedules); imputed income calc (GTL > $50K Table I rates, domestic-partner fair-market value) → taxable elements; mid-cycle change proration policy per plan.

## 7. Compliance
ACA 1094-C/1095-C data assembly (offer codes, affordability safe harbors) with e-file vendor handoff; Section 125 plan-doc alignment checks; HIPAA boundary: health-plan data segregated access tier, minimum-necessary enforcement, no health detail in analytics below suppression thresholds; ERISA SPD distribution tracking; country statutory benefits registers (IN gratuity provisioning data → Finance).

## 8. Events & APIs
Events: enrollment.created/changed/terminated, lifeevent.opened/closed, eligibility.gained/lost, eoi.status.changed. APIs: GET /workers/{id}/enrollments; POST /life-events; GET /deductions?pay_period= (PAY snapshot endpoint).

## 9. Edge Cases Register
Rehire within stability period (ACA continuity); dual-covered couples both employed here (dependent conflict rules); retro divorce reported late (coverage clawback policy + carrier retro term limits); mid-OE termination; leave-of-absence premium handling (pay-by-check vs. arrears vs. employer-pays per leave type); EOI denied after default coverage started; acquisition population mid-plan-year (mirror-plan bridging).

## 10. Open Questions
COBRA: outsource (recommended) vs. native administration. Global benefits beyond payroll-deduction scope (e.g., country medical schemes) — data-of-record only vs. administered. Decision month 3.

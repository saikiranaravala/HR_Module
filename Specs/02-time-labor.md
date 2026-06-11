# Deep-Dive PRD 02 — Time & Labor + Absence Management
*Project Meridian | Depends on: 01-Core, 12-Platform rules engine | Feeds: 03-Payroll Hub, 11-Analytics*

## 1. Mission & Success Metrics
Capture, calculate, and certify every compensable minute and every absence under per-jurisdiction rules — with zero payroll-cycle delays caused by time data.
- Timesheet completion by period close: ≥ 99.5% (auto-escalation handles the tail).
- Time-calc rule defects reaching payroll: 0 critical per quarter (simulator-gated releases).
- Mobile punch P95 < 2 s including geofence check; offline punch sync loss: 0.

## 2. Time Capture
- **Capture modes** (policy-assigned per population): punch (web/mobile/clock), elapsed entry, exception-only (schedule auto-fill; employee certifies or edits). Mode can vary by worker even within a department.
- **Mobile punch:** geofenced (configurable radius per location, soft-warn vs. hard-block), offline queue with conflict resolution, photo/biometric option per local law (biometric consent registry; disabled where prohibited, e.g., IL BIPA risk posture decided per legal).
- **Clock integration:** adapter spec for major hardware (UKG/Kronos 4500 series legacy, modern REST clocks); heartbeat monitoring; store-and-forward.
- **Web/desktop:** weekly grid with templates, copy-last-week, project/cost allocation rows, attestation prompts at submit (CA meal-break attestation text configurable per state).

## 3. Rules Engine Requirements (the heart)
Rules are versioned, effective-dated configuration executed by the shared platform rules engine.
- **Overtime templates:** US FLSA weekly 40; California daily (8/12 doubletime, 7th-day rules); Colorado 12-hr daily; EU Working Time Directive (48-hr average over reference period — tracking + alerting, not pay calc); IN Factories Act daily/weekly caps; union CBA variants (consecutive-day, weekend multipliers).
- **Premiums:** shift differentials (time-band or shift-code based), on-call retainers, call-back minimums, meal/rest-break penalty pay (auto-detected from punch gaps per CA rules), holiday worked multipliers with holiday-calendar resolution by location.
- **Rounding:** punch rounding policies (nearest 5/6/15 with grace) — flagged jurisdiction-sensitive; default = no rounding (litigation-safe).
- **Rule simulator (P0):** replay any historical period for any population against a draft ruleset; diff report of pay-impacting changes; required sign-off artifact before promotion to prod. **Acceptance:** simulate 10K workers × 1 period < 10 min.
- **Determinism & explainability:** every calculated result line links to the rule version + input punches that produced it ("explain this 1.5× line" view for managers and auditors).

## 4. Absence & Accruals
- **Accrual engine:** formulas by hours-worked, per-period grant, tenure bands, anniversary vs. calendar vs. fiscal year basis; caps, carryover (with expiry lots — FIFO consumption), negative-balance limits, accrual while on leave rules per type.
- **Balance projection service:** "balance as of future date X given pending requests" — powers ESS UX and prevents the #1 HR question.
- **Statutory leave catalog:** per-country types with entitlement calculators (UK 5.6-week statutory holiday incl. irregular-hours accrual method; FR RTT; DE Urlaub carry rules; IN earned/casual/sick splits per state Shops Acts; US state sick-leave laws by worksite — auto-resolved from location).
- **Request flow:** ESS request → policy validation (notice periods, blackout windows, team-coverage conflict view) → approval → calendar + payroll-period integration; cancellation/modification rules post-approval; half-day/hour-granular per policy.
- **Disability/parental interplay:** absence type transitions (STD → LTD), concurrent designation (FMLA running concurrent with paid leave), and pay-phase timelines visible to employee.

## 5. Scheduling (P1)
Shift templates, rotation patterns (e.g., 4-on-4-off), publication SLAs (predictive-scheduling laws: OR/Seattle/NYC fair-workweek — publication lead time + predictability-pay triggers as rules), open-shift marketplace (qualify-check: certifications from LEARN, rest-period validation, OT-projection warning), swap workflow with symmetric validation.

## 6. Period Close & Payroll Handoff
1. Period lock T-2 days before payroll transmit (per pay-group calendar).
2. Exception sweep: missed punches, unapproved time, WTD breaches → manager queue with bulk-fix; unresolved at lock = policy decision per group (pay-as-scheduled + retro vs. hold).
3. Manager certification (attestation logged) → results compiled to canonical payroll elements (earnings code × hours × rate context) → PAY-3 validation gate.
4. Post-lock edits → retro engine: delta calculation vs. paid results, routed as retro elements next cycle with full lineage.
- **Acceptance:** zero manual file manipulation between TIME and PAY; retro deltas mathematically reconcile (original + delta = recalculated) in automated tests.

## 7. Events & APIs
Events: timesheet.submitted/approved, period.locked, absence.requested/approved/cancelled, accrual.posted, wtd.breach.detected. APIs: GET /workers/{id}/balances?as_of; POST /timesheets/bulk; GET /time-results?pay_period= (PAY consumption endpoint, idempotent snapshot per cycle).

## 8. Edge Cases Register
Midnight-spanning shifts (attribution rules per jurisdiction); DST transitions (23/25-hr days — store UTC + local, pay rules on local); transfer mid-period across pay groups (split-period results); retro pay-rate change re-pricing locked periods; multi-job workers with combined-hours OT aggregation rules (FLSA joint employment); minors' hour caps blocking schedule publication; leave during notice period.

## 9. Open Questions
Physical clock estate: replace vs. integrate legacy devices per site (survey in month 1). Predictive-scheduling AI (demand forecasting) — confirm P2 scope and data sources (POS/volume feeds).

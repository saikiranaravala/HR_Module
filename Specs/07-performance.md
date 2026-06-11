# Deep-Dive PRD 07 — Performance Management
*Project Meridian | Depends on: 01-Core, 12-Platform | Feeds: 05-Comp (ratings), 09-Succession (talent data)*

## 1. Mission & Success Metrics
Goal alignment, fair evaluation, and continuous feedback that managers actually use — with calibration integrity and audit-grade rating lineage.
- Review-cycle on-time completion ≥ 98%; check-in cadence adoption ≥ 70% quarterly.
- Calibration adjustments fully audited: 100% of rating changes carry actor + rationale.
- Manager time per review −40% via AI drafting (measured via instrumentation).

## 2. Goal Management
- Goal object: title, description, type (OKR with key results / MBO / development), weight, measure (quant target + unit, or milestone set), alignment link (parent goal up the cascade), visibility (private/manager/public), status + progress updates with timestamps.
- Cascading: company goals published → org translation → team/individual alignment; alignment map visualization (who supports what); orphan-goal report (no alignment) for leaders.
- Lifecycle: mid-cycle revision with version history (original preserved); goal transfer on manager/worker moves (policy: travel-with-worker vs. re-baseline); bulk goal assignment for standard roles (e.g., support reps inherit team goals).
- Integrations: progress auto-update connectors (P2): Jira epic completion, CRM quota attainment.

## 3. Review Cycles
- Template designer: sections (goals assessment, competencies from job profile with anchored proficiency scales, values, overall), rating scales per section (configurable n-point with behavioral anchors; supports ratingless mode — narrative + calibration-grid only, pending philosophy decision), participant matrix (self, manager, skip, matrix manager weight-in), language per population.
- Cycle types: annual/semi-annual focal; probationary (auto-instantiated from hire +X days, with extend/pass/fail outcomes feeding Core actions); PIP (HR-gated creation, milestone checkpoints, outcome documentation with legal-review flag and retention rules).
- Process flow: launch (population snapshot + late-hire/leaver rules: pro-rated eligibility, auto-exclusion < 90 days tenure) → self-assessment window → manager assessment (AI draft from goal progress + feedback history + check-in notes, clearly labeled, edit-required-before-submit policy option) → calibration → approval → release with acknowledgment (employee comment field, signature, dispute-process link) → lock + archive to talent profile.
- **Calibration mode:** facilitated session view — distribution histograms vs. guideline, drag-to-adjust grid with live distribution recompute, side-by-side comparees, mandatory rationale on every adjustment, session minutes artifact auto-generated, pre/post snapshots immutable.
- **Acceptance:** cycle launch for 50K computes population + instantiates docs < 30 min; calibration grid for 500-person org loads < 3 s.

## 4. Continuous Performance
Check-ins: scheduled cadences (manager-worker), shared agenda + private notes, topic templates (growth, wellbeing, workload), history timeline feeding review-time AI summarization. Real-time feedback: request (choose raters + competencies) / give unsolicited / praise (public wall opt-in, values-tagged); feedback visibility rules (to-subject vs. to-manager — explicit per item, no silent manager-visible feedback). 360 campaigns: rater nomination with approval, anonymity threshold (no theme shown < 3 raters), external-rater email flow, narrative + competency aggregation report, coach/HR-mediated release option for sensitive levels.

## 5. AI Capabilities (governed per 14-AI)
Draft assist (self + manager narratives, labeled, full edit); bias-language lint pre-submit (flags gendered/age-coded terms, idiosyncratic-rater patterns like personality-vs-behavior language); rating-pattern analytics for HR (leniency/severity drift by manager, year-over-year anomaly flags) — aggregate views, never auto-adjusting ratings; check-in summarizer at review time with citations to source notes. Hard rule: AI never assigns or recommends a rating value.

## 6. Security & Records
In-flight docs visible only to participants + HRBP scope; PIP docs tier-restricted with read-audit; released reviews retained per country schedule (and excluded from GDPR erasure during retention with legal basis recorded); litigation hold integration freezes documents + feedback trails.

## 7. Events & APIs
Events: cycle.launched, review.submitted/released/acknowledged, checkin.completed, feedback.given, pip.opened/closed. APIs: GET /workers/{id}/performance-summary (Comp + Succession consumption: latest rating, trend, 9-box inputs); goal CRUD; calibration session APIs.

## 8. Edge Cases Register
Manager change mid-cycle (handoff rules: outgoing drafts → incoming finalizes, both logged); worker on leave during window (auto-extension per leave type + country law); rating released then factual error found (amendment workflow with dual record); skip-level disagreement protocol; matrix-manager weighting conflicts; terminated-before-release docs (close-out policy).

## 9. Open Questions
Ratings philosophy (master §13.4) — template defaults blocked on this; recommend decision workshop month 4. Forced distribution: hard enforcement vs. guideline-only (recommend guideline-only + calibration transparency).

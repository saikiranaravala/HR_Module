# Training 08 — Change Management Lead

**Audience:** change, communications, and training-delivery leads for the PeopleSoft → Meridian program. **Duration:** 2 days. **Prerequisites:** change-management background; Trainings 01–02 hands-on.

## Learning Objectives

Position the change credibly (what's familiar, what's genuinely different); build the persona impact map and wave-aligned rollout plan; run the champion (super-user) network; measure adoption with the system's honest metrics; handle the consultation obligations and program gates that constrain your plan.

---

## Day 1 — The Change Story & The Plan

### 1.1 Why this migration is easier to sell than most

The UI deliberately keeps **PeopleSoft's navigation grammar** — dark header band, homepage selector, tile homepages, breadcrumb bar, dense classic grids with Personalize/Find/View All, gold/amber action buttons. A 20-year PS user recognizes the furniture immediately. Lead with this: *"you already know how to drive it."*

What's genuinely new (the value story, per persona):

| Persona | Headline change | Proof point in the demo |
|---|---|---|
| Employee | Answers, not tickets | Payslip explains its own delta; copilot answers policy questions scoped to *your* country |
| Manager | Decisions with context | One inbox, context inline, 2-click approvals, live comp budget bar |
| HR admin | Trust the record | Effective-dated history, loud payroll gates, certified snapshots |
| Everyone | Fewer clicks | Ctrl+K palette, "needs your attention" deep links, 2-click PTO |

### 1.2 What people will resist (prepare answers, don't improvise)

| Objection | Honest answer |
|---|---|
| "I can't edit history anymore" | Correct — corrections are new rows. It's what makes the record defensible in disputes *for you* |
| "The system blocked my payroll batch" | The gate caught an anomaly; the old system would have paid it wrong silently |
| "AI is watching/judging us" | AI never rates performance, never rejects candidates, and inherits *your* permissions — show `use_cases.yaml` governance to works councils |
| "Analytics hides my numbers" (n<5) | Privacy suppression protects small teams — including yours |
| "Where did my customizations go?" | Business variation moved to versioned configuration — changes now take days, not release cycles |

### 1.3 Rollout structure

Waves follow the program build order (foundation → core HR → operational core → talent suite) and the migration factory's wave map. Per wave: T-6w comms launch → T-4w super-user certification (Training 03) → T-2w end-user training (01/02, delivered by super users with your support) → T-0 cutover (Training 11 owns the mechanics) → T+2w hypercare with daily triage → T+6w adoption review against metrics.

**Constraint you must plan around:** the wave map itself is gated by two open program decisions (payroll provider RFP; works-council inventory). Build your plan wave-relative ("T-6w"), not calendar-absolute, until gates close.

## Day 2 — Champions, Metrics & Obligations

### 2.1 The champion network = the super users

Training 03 certifies at least two super users per country before their wave. They are your delivery arm: they co-teach 01/02 locally, staff hypercare, and feed the objection list back to you. Budget their time formally (≈25% during their wave window) — an unfunded champion network is a name list, not a network.

### 2.2 Adoption metrics (the system computes them honestly — use that)

| Metric | Source | Watch for |
|---|---|---|
| Copilot deflection rate | Service delivery — counted **honestly**: a case reopened within 72h is *not* deflected | Deflection climbing while reopens climb = bad KB, not adoption |
| Approval cycle time | Workflow instances | Should drop within 2 weeks of MSS adoption |
| ESS transaction share | Cases opened vs self-service completions | The real "did tickets die" number |
| Training completion | Learning module (compliance engine tracks it like any assignment) | Overdue escalation ladder is automatic |
| Palette usage / deep-link follows | UI analytics | Low usage = re-teach navigation, not more email |

Anti-metric warning: do **not** report raw copilot answer volume as success — the deflection definition exists precisely because that number lies.

### 2.3 Consultation & compliance obligations

- **Works councils (DE/FR/NL noted in the program):** monitoring-adjacent features (audit logging visibility, analytics, AI use cases) may require consultation *before* the wave. The works-council inventory is an open gate — coordinate dates with the program office, and use the governance artifacts (registered AI use cases, suppression rules, T2/T3 read-logging) as your consultation pack. They are genuinely reassuring.
- **Training content localization:** UI strings are externalized by design; your materials must match wave languages. Screenshots come from the demo dataset only — never production data in decks, ever (Invariant #8 applies to slides too).
- **Certification records:** deliver sign-off checklists (each Training doc's last section) into the learning module as evidence-backed completions — the compliance engine then tracks who is trained, with the same rigor as statutory training.

### 2.4 Hypercare exit criteria (per wave)

Exit hypercare when, for 10 consecutive business days: no P1/P2 incidents attributable to user error; deflection ≥ target with stable reopen rate; approval cycle time at or below baseline; super users report objection list stable (no new categories). Publish the exit decision — ambiguity about "are we done" burns trust.

---

## Competency Checklist (sign-off)

- [ ] Delivers the 10-minute change story per persona using only demo-environment evidence
- [ ] Answers all five stock objections without notes
- [ ] Produces a wave plan that is gate-aware (wave-relative dates)
- [ ] Stands up a funded champion roster with certification dates
- [ ] Defines the metric dashboard incl. the honest-deflection caveat
- [ ] Assembles a works-council consultation pack from governance artifacts

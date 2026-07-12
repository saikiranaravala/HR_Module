# Training 04 — Functional Consultant (Configuration & Implementation)

**Audience:** implementation consultants who configure Meridian for a customer/population: rules, workflows, country packs, comp structures, templates. **Duration:** 5 days. **Prerequisites:** HCM domain experience; Trainings 01–03 recommended.

## The One Rule That Defines Your Job

**Invariant #5 — Configuration-only extensibility.** All business-logic variation lives in versioned, effective-dated, testable configuration: decision tables and workflow definitions. There are **no scripting hooks, no code forks, no per-customer branches, no per-country `if` statements** — this is the anti-PeopleCode rule and it is load-bearing. If a requirement seems to need code, the answer is: raise it with the technical team as a product gap; never work around it.

Corollary (Invariant #1): configuration is **effective-dated like data**. A rule change takes effect on a date; historical transactions keep the rule version that computed them.

## Learning Objectives

Author and version decision tables; author workflow definitions; build country packs; configure comp structures, performance templates, and jurisdiction packs; write the mandatory decision-table tests and golden-dataset regressions; run a config release safely.

---

## Day 1 — The Configuration Model

### 1.1 Where configuration lives

Each module owns a `config/` directory. The live inventory (study these as worked examples):

| Config | Path | Teaches you |
|---|---|---|
| Rulesets (decision tables) | `src/rules_workflow/config/rulesets/` — `overtime-eligibility`, `overtime-thresholds`, `fmla-eligibility`, `benefits-eligibility`, `minor-hour-caps`, `transfer-pattern`, `case-routing` | Table shape, versioning, effective dates |
| Workflow definitions | `src/rules_workflow/config/workflows/` — `job-change-approval`, `comp-change-approval` | Steps, roles, fallback queues, escalation |
| Comp structures | `src/compensation/config/` — `guidelines.yaml`, `geo_zones.yaml`, `components.yaml` | Guideline matrix, zones, pay components |
| Performance templates | `src/performance/config/templates.yaml` (+ `bias_lint.yaml`) | Ratingless mode isolation |
| Learning jurisdiction packs | `src/learning/config/jurisdiction_packs.yaml` (CA SB1343, NY, OSHA seeded) | Statutory recurrence, population rules |
| Recruiting packs | `src/recruiting/config/` — `stage_flows`, `knockout`, `pay_transparency`, `retention` | Stage config, deterministic screens, disclosure |
| Notifications & country packs | `src/ess_mss/config/` — `notifications.yaml`, `alumni.yaml` | Channel rules, country retention |
| Policy roles | `src/platform_core/config/policy/roles.yaml` | Capabilities, tiers, scopes (change via security review only) |
| AI use cases & prompts | `src/ai_layer/config/` — `use_cases.yaml`, `prompts.yaml` | Governed AI registration |

### 1.2 Anatomy of a decision table

Open `overtime-eligibility.yaml` and identify: ruleset id, **version**, **effective date**, input columns, condition rows (first-match or all-match semantics), outputs, and the default row. Key disciplines:

- **Never edit a live version in place** — add a new version with a new effective date. Old transactions keep old versions (the payslip's "rule v3" note is this system working).
- **Exhaustiveness:** every input combination must land somewhere; the default row is your safety net and its output must be safe (deny/route-to-human), never permissive.
- **Country variation = more rows or a country-keyed pack**, never a second ruleset fork per country unless the domains genuinely differ.

**Exercise 1.2** — Add a new version of `overtime-eligibility` effective next month with one changed threshold. Verify a past-dated evaluation still uses the old version.

## Day 2 — Workflow Design

Study `comp-change-approval.yaml`:

- **Steps** name a resolver (manager-of, role, skip-level) — not a person. People change; resolution logic doesn't.
- **Role-queue fallback:** a step that resolves to nobody routes to `role:X` — visible to everyone holding the role. Never design a workflow that can strand an item.
- **Escalation & SLA** per step; **delegation** is handled by the platform (30-day cap, self-approval block) — do not re-model it inside a workflow.
- **Conflict-of-interest patterns:** the skip-level self-recommendation route in comp is a workflow pattern you'll reuse (approver == subject → escalate one level).
- **Bulk-barred flags** mark step types that must never be bulk-approved (comp).

**Exercise 2.1** — Author a `learning-spend-approval` workflow: manager → (if >$1,000) role:l&d-partner, 3-day SLA, escalation to skip-level, self-approval blocked. Test it with the demo cast.

## Day 3 — Country Packs & Domain Configuration

### 3.1 Country packs

A country pack is versioned config/content keyed by jurisdiction: statutory rules (jurisdiction packs in learning), retention clocks (recruiting `retention.yaml`, ess_mss `alumni.yaml`), disclosure duties (`pay_transparency.yaml`), notification consent rules (frontline consent in `notifications.yaml`).

Pattern to internalize from `jurisdiction_packs.yaml`: **population rules** (who it applies to — worker types matter: employees vs contractors), **recurrence** (rolling anniversary vs fixed date — the platform provides real calendar-month arithmetic; never approximate months as 30 days), **escalation ladder**, and **consequence flags** (Learning flags; the policy layer gates — a module never blocks access locally).

### 3.2 Compensation & performance configuration

- `guidelines.yaml` isolates the **ratings-philosophy gate**: the guideline matrix takes an *opaque rating input* — if the customer goes ratingless, only this file changes.
- Same isolation in `templates.yaml` (performance): **ratingless mode is a template switch**, not a code change.
- `geo_zones.yaml` + `components.yaml`: zones map locations to differentials; the components catalog defines every pay element a comp record can carry.
- **AI boundary you configure around:** nothing you configure may create a path where AI assigns or recommends a rating, or auto-rejects a candidate. Use cases must be registered in `use_cases.yaml` — an unregistered use case cannot reach a model at all.

## Day 4 — Testing & Release Discipline (non-negotiable)

Config ships like code:

1. **Decision-table unit tests** — every rule row exercised at least once; boundary values on every numeric threshold.
2. **Golden-dataset regression** — a fixed input population with expected outputs (the TIME simulator pattern); a new ruleset version must pass 100% or explain every diff as intended.
3. **Edge-case register coverage** — the domain PRD's register rows that touch your config must have named tests (e.g., `test_TIME_midnight_spanning_punch`).
4. **Effective-date tests** — old date → old version, new date → new version, gap coverage.

Release flow: author on branch → tests green (`.\.venv\Scripts\python.exe -m pytest src/test/<module>`) → peer review citing the requirement ID (e.g., "expands TIME-2") → merge → the release notes name every ruleset version bump. Emergency change = same flow, faster humans — there is no "hotfix in the admin UI" path, by design.

## Day 5 — Requirement Traceability & Program Gates

- Every configuration decision traces to a requirement ID from the master PRD (`Specs/PRD-Meridian-HCM.md`); domain detail lives in the domain PRD (`Specs/01`–`16`). **If no requirement covers what a customer asks for, flag it — don't invent scope.**
- **Check the open gates before designing** (`Specs/00-INDEX.md`): payroll provider RFP, ratings philosophy, ATS/LMS build-vs-buy, IN/CN residency rulings, works-council inventory. If your work area is gated, design so both outcomes survive (the guideline-matrix isolation is the model).
- Deliverables follow the PRD house style: requirements with acceptance criteria, data/config model, workflows, edge-case register, open questions.

---

## Competency Checklist (sign-off)

- [ ] Versions a decision table with a future effective date; proves old transactions keep the old version
- [ ] Authors a workflow with role fallback, SLA, escalation, and self-approval block
- [ ] Builds a country-pack entry with population rule + recurrence + escalation
- [ ] Explains how the ratings gate is isolated (two file names)
- [ ] Writes decision-table tests + golden regression; runs the module suite green
- [ ] Explains why there are no scripting hooks — and what to do when config seems insufficient
- [ ] Names the five program gates and how to design around an open one

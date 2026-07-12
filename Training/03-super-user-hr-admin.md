# Training 03 — Super User / HR Administrator (Workforce Administrator)

**Audience:** HR operations, payroll administrators, benefits administrators — the people who run HR daily and are first-line experts for their country/region. **Duration:** 3 days. **Prerequisites:** Trainings 01–02.
**Demo persona:** **Sam Rivera** (HR Operations Lead) — select *Workforce Administrator*.

Super users are also the **champion network**: after certification you are the first escalation point before IT, and you co-deliver end-user training in your wave (see Training 08).

## Learning Objectives

Execute core HR transactions with correct effective dating; run the payroll interface cycle and clear its gates; administer benefits events; operate case management within privacy boundaries; read certified analytics; perform sanctioned data corrections; know exactly where your authority ends (and why).

---

## Day 1 — The Temporal Backbone & Core HR Transactions

### 1.1 How Meridian stores people data (90 min — the most important lesson)

Every person/job/comp/org record is **effective-dated**: `effective_date` + `effective_sequence` + action + reason, with full audit capture. Consequences you must internalize:

| Situation | What you do | What the system records |
|---|---|---|
| New hire | Enter with hire effective date | New row, action=Hire |
| Promotion effective July 1 | Enter anytime with eff-date 07-01 | Future-dated row; visible now, active then |
| **Correction** — same-day fix of a wrong entry | Correct the record | New row, same eff-date, **sequence +1**, action=update-correction; the wrong row stays in history |
| **Retroactive change** — e.g. missed April merit | Enter with the April eff-date | Retro row + **retro event** so downstream (payroll!) recalculates; never a silent rewrite |
| Rehire | Rehire action | Original hire date is **bridged**, not overwritten |

**You cannot edit or delete history.** Database triggers physically reject UPDATE/DELETE on temporal rows. If someone asks you to "just fix" an old row — the answer is a correction row or a retro transaction, always.

**Exercise 1.1** — In the demo data, find the worker with a same-day correction (two rows, seq 0 and 1, salary corrected to 96,500). Run an as-of query in the UI for that date and confirm the seq-1 value wins.
**Exercise 1.2** — Enter a retroactive comp change; then find the retro event it emitted.

### 1.2 Org & position management (60 min)

Departments and positions are effective-dated like people. Transfers between org subtrees re-scope everything automatically (manager dashboards, analytics, succession slates flag for review). Org paths are hierarchical (`/corp/eng/data`) — access follows the subtree.

### 1.3 Approvals administration (45 min)

You see workflow instances across your population: stuck items, role-queue depth, SLA breaches. You can **reassign** a step (audited) but never **skip** one — if a workflow is wrong, the fix is a config change by a functional consultant (Training 04), not a bypass.

## Day 2 — Payroll Interface & Benefits

### 2.1 Payroll hub operations (half day)

Meridian is a **payroll integration hub** — it prepares, validates, and reconciles inputs/results with providers; it does not compute net pay itself.

**The cycle state machine:** each pay cycle moves through collect → validate → transmit → results → reconcile → lock. Your console shows every cycle by country/population and its state.

| Gate you operate | What it means |
|---|---|
| **Held input** | An input flagged unsafe to send (e.g., bank-change freeze pending verification) — resolve or consciously release |
| **Anomaly gate** | Statistical outliers (e.g., net swing > threshold) halt the batch **loudly**; you review each anomaly and release or pull it |
| **Negative net / arrears** | Deductions exceeding pay create an arrears record with a recovery schedule — never a silent negative |
| **Off-cycle runs** | Final pay for terminations, corrections — same gates, expedited path |
| **Retro deltas** | A locked period's change flows as original + delta pair; **reconciliation identity: original + retro delta = recalculated** — the system proves it, you verify the report |

**The prime directive:** the pipeline **halts loudly or proceeds provably; it never degrades quietly**. A halted cycle is the system working. Your job is triage, not bypass — there is no "force send" and that is deliberate.

**Exercise 2.1** — Work the demo cycle: release the bank-freeze held input incorrectly (it re-flags), correctly (verification path), review the arrears case, and confirm the off-cycle final-pay supplement reconciles.

### 2.2 Benefits administration (half day)

- **Eligibility & waiting periods** are rules (e.g., "first of month strictly after hire + N days" — hire on the 1st still rolls forward). You read rule outcomes; consultants change rules.
- **Enrollment states you manage:** active, pending-EOI, defaulted (missed OE window → default plan), waived, terminated mid-OE (cancels pending elections).
- **Life-event verification:** you approve documentation; the effective date follows the event (birth backdates).
- **Retro divorce / clawback window:** a late-reported divorce ends dependent coverage retroactively; premium clawback runs within the policy window. The demo has this case — walk it.
- **Dual-covered dependent conflict:** the system flags a dependent covered by two employees; resolution workflow assigns primary coverage.

## Day 3 — Service Delivery, Analytics & Boundaries

### 3.1 Case management & knowledge (half day)

- **Routing is a decision table** (`case-routing`): category + population → queue + SLA. You monitor queues, rebalance load, and watch SLA dashboards.
- **ER (employee relations) cases are T3-segregated:** only the `er-investigator` role opens them; **every read is audit-logged**; case notes have explicit visibility levels (worker-visible vs internal).
- **Legal hold:** a worker/division under hold freezes changes; the system enforces it — you'll see blocked transactions with the hold reference.
- **Knowledge base:** articles carry a legal-review gate before publishing and a 12-month staleness alert. Stale articles are the #1 cause of bad copilot answers — treat the staleness queue as production maintenance.
- **Alumni access:** terminated workers get scoped grants (payslips, tax docs) — time-boxed, not full ESS.

### 3.2 Analytics & reporting (90 min)

- **Certified snapshots are immutable** — a certified headcount number never changes after the fact. Corrections create a **restated version** alongside the original (restatement-by-version), so "the number the board saw" is always reproducible.
- **Retro changes restate facts** in the live model but never touch certified snapshots.
- **Reorg bridging:** after a reorg, trend lines use the org bridge for like-for-like comparison.
- **Suppression** (n<5, complementary) applies to you too — admin roles do not bypass privacy math.

### 3.3 Where your authority ends (60 min — mandatory)

| You cannot | Who can | Why |
|---|---|---|
| Edit/delete history rows | Nobody | Immutability is enforced by the database |
| Change a business rule or workflow | Functional consultant via config release | Config is versioned & tested, not ad-hoc |
| Read ER cases without the role | ER investigators | T3 segregation |
| See suppressed analytics cells | Nobody | Privacy by construction |
| Bypass the payroll anomaly gate | Nobody | Loud-halt principle |
| Grant yourself roles | Security admin via policy config | Separation of duties |

**The audit chain protects you:** every sensitive action you take is hash-chained. If a dispute arises about "who changed what when," the chain is your evidence. `GET /v1/audit/verify` proves the chain is intact — Training 07 owns running it; you should know it exists.

---

## Competency Checklist (sign-off)

- [ ] Executes hire, future-dated transfer, same-day correction, and retro comp change — each with correct effective dating
- [ ] Explains correction-vs-retro to an end user in one sentence each
- [ ] Runs a payroll cycle end-to-end in the demo, clearing held input and anomaly gates correctly
- [ ] Explains the reconciliation identity and finds it on the retro report
- [ ] Processes a life event with retroactive effective date and an EOI-pending election
- [ ] Routes, reassigns, and closes cases; explains ER segregation and note visibility
- [ ] Explains certified-snapshot restatement to a manager who asks "why are there two numbers?"
- [ ] Recites the six authority boundaries above without notes

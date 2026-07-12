# Training 01 — End User: Employee (Employee Self Service)

**Audience:** every employee. **Duration:** 2 hours (self-paced or instructor-led). **Prerequisites:** none.
**Demo persona:** log in as **Avery Quinn** (Senior Platform Engineer) — select *Employee Self Service* in the homepage selector.

## Learning Objectives

After this course you can: navigate Meridian and find anything in under 3 clicks; read and understand your payslip including period-over-period changes; request time off; manage benefits elections and life events; view and verify your own job and pay history; use the Help Center copilot and know when a human takes over.

---

## Module 1 — Getting Around (20 min)

| Element | What it does |
|---|---|
| **Homepage selector** (top-left dropdown) | Switches workspaces. Employees see *Employee Self Service*; managers and HR see additional homepages |
| **Left navigation** | Work centers grouped by area (Workspaces, Self Service). The hamburger (☰) collapses it |
| **Ctrl+K command palette** | Fastest path to anything: type a page name, an action ("request time off"), or a person's name |
| **Breadcrumb bar** | Shows where you are; click the homepage name to return |
| **Needs your attention** (Home) | Deadline-driven items: expiring PTO carryover, due trainings, pending acknowledgments |
| **KPI tiles** (Home) | One-glance numbers: next payday and net, PTO balance, benefits plans, goal progress, open learning, help cases |

**Exercise 1.1** — Press `Ctrl+K`, type "pay", open Payslips. Return home via the breadcrumb. Open Time & Absence through the left nav. Find "Jordan Patel" through the palette.

## Module 2 — Understanding Your Pay (25 min)

Open **Payslips**. The most recent payslip shows earnings, deductions, taxes, and year-to-date columns.

- **The delta note:** when your net changes versus the prior period, the payslip *tells you why* in plain language (e.g., "Net is $96.40 lower than last period: your benefits Open Enrollment elections started this cycle"). Read it before calling HR — it usually answers the question.
- **Line-level notes:** hover/expand a line to see its rule source, e.g. overtime shows "2.5h @ $38.33 (FLSA weekly-40, rule v3)" — the exact versioned rule that computed it.
- **What you will never see here:** another employee's pay. Access is enforced identically in the UI, reports, APIs, and the copilot.

**Exercise 2.1** — Open the May 16–31 payslip. Answer: why is net lower than the prior period? What rule version computed the overtime line? What does the GTL imputed-income line represent (read its note)?

## Module 3 — Time Off & Absence (25 min)

Open **Time & Absence**.

- **Balances by lot:** PTO, PTO carryover (with expiry date), Sick. Expiring lots are flagged amber on the home tile too.
- **Requesting time off (2 clicks from home):** *request time off* link → pick dates → the form shows a **balance projection** ("Balance after: X days") *before* you submit. Requests draw from expiring lots first.
- **Team calendar:** you can see teammates' absence *days* (not reasons — reasons are private).
- **After submitting:** the request routes to your manager via workflow. You'll see its status; you can cancel while pending.

**Exercise 3.1** — Request 3 days of PTO before June 30. Confirm the projection uses your expiring carryover first. Cancel the request afterwards.

## Module 4 — Benefits (20 min)

Open **Benefits**.

- **Current elections** show plan, option, coverage tier, and your per-pay cost.
- **Life events** (marriage, birth/adoption, divorce, dependent aging out) open a change window outside Open Enrollment. Changes are effective-dated — a birth event backdates coverage to the birth date.
- **Evidence of Insurability (EOI):** some life-insurance increases are *pending* until the carrier approves; the status is shown. If denied, coverage reverts to the default automatically.

**Exercise 4.1** — Locate your medical election's per-pay cost and confirm it matches the payslip deduction from Module 2.

## Module 5 — Your Profile & Job History (15 min)

Open **Personal Details**.

- **Job history is temporal:** every row has an effective date and action (Hire, Promotion, Comp change, Transfer). Two rows on the same date carry sequence numbers — corrections don't erase history, they add a row.
- **The as-of date picker** answers "what was true on date X?" — set it to a past date and the page shows your job as of that date.
- **Bank changes have a fraud interlock:** changing bank details triggers verification and a notification to your other channels. This is deliberate; do not be alarmed by the extra step.
- **Future-dated changes** (e.g., an approved transfer effective next month) are visible with their future effective date.

**Exercise 5.1** — Using the as-of picker, answer: what was Avery's job title and department on 2023-01-01? On what date does the Data Platform transfer take effect?

## Module 6 — Performance, Learning & Growth (15 min)

- **Performance:** view goals (with cascade alignment), log check-ins, submit and receive feedback. Private check-in notes are visible only to their author. If your company runs review cycles, you acknowledge released reviews here.
- **Learning:** assigned compliance trainings show due dates and escalation state; the home tile flags overdue items. Completions are evidence-backed — the certificate records the exact content version you completed.
- **AI drafting help:** where drafting assistance is offered (e.g., self-review), the draft is labeled as AI-assisted and **you must edit it before submitting** — verbatim submission is blocked.

## Module 7 — Getting Help (10 min)

Open **Help Center**.

- **Ask the copilot first:** it answers from your company's policy content, scoped to *your* country/population — you will never receive another country's policy answer.
- **When the copilot hands off:** if it's uncertain, if sources contradict, or if you ask — a case is created with the transcript attached, routed by category with an SLA.
- **Case notes:** you see agent updates; internal investigation notes are not visible to you (and that's shown honestly in the UI).

**Exercise 7.1** — Ask the copilot about PTO carryover expiry. Then create a case from the conversation and find its SLA.

---

## Competency Checklist (sign-off)

- [ ] Navigates to any page in ≤3 clicks or one palette search
- [ ] Explains a payslip delta using the delta note and line notes
- [ ] Submits and cancels a PTO request; reads the balance projection
- [ ] Locates benefits elections and reconciles them to the payslip
- [ ] Uses the as-of picker to answer a historical job question
- [ ] Knows the three things AI assistance will never do (approve, rate, reject)
- [ ] Escalates a copilot conversation to a case

## FAQ

**Why do I see "this read was logged" on some pages?** Sensitive data reads (your own comp history included) are audit-logged for everyone, including HR and admins. It protects you.
**Can my manager see my sick-leave reason?** No — managers see absence days, not reasons or diagnoses.
**Why can't I just edit my old address record?** History is immutable. You add a change with an effective date; the old value stays in history. That's what makes your record auditable and defensible.

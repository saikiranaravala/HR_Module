# Training 02 — End User: Manager (Manager Self Service)

**Audience:** people managers. **Duration:** 3 hours. **Prerequisites:** Training 01.
**Demo persona:** **Morgan Lee** (Director, Platform Engineering) — select *Manager Self Service*.

## Learning Objectives

Work the unified approvals inbox efficiently and safely; delegate correctly; run team time/absence; complete a comp cycle worksheet within guardrails; work a requisition pipeline with governed AI assistance; read team analytics and understand privacy suppression; contribute to talent reviews with defensible rationale.

---

## Module 1 — The Approvals Inbox (40 min)

Open **Approvals**. Everything routed to you — time, absence, job changes, comp, requisitions, learning spend — lands in one inbox, each item carrying **decision context** so you rarely need to open another screen:

| Item type | Context shown inline |
|---|---|
| Absence | Balance after approval, team conflicts on those dates |
| Timesheet | OT hours and the exact rule version that computed them |
| Comp change | Compa-ratio before → after, guideline position, justification |
| Job change | Position number, budget check result |
| Learning spend | Remaining team budget |

**Rules the inbox enforces (don't fight them — they're load-bearing):**
- **One-click approve** for routine items; **bulk approve** for everything routine at once.
- **Comp items are excluded from bulk** (`bulk barred`) — a merit increase flagged *out of guideline* must be opened and decided individually. The guardrail (e.g., "Merit +9% → $98,100, out of guideline; justification: retention risk") is surfaced *before* you commit.
- **Role-queue fallback:** if a step has no individual assignee, it routes to a role queue (e.g., `role:hr-partner`) — items you see because of your role are labeled as such.
- **Approve/reject requires no navigation** — but "reject" requires a reason, which the requester sees verbatim. Write it for their eyes.

**Exercise 1.1** — Bulk-approve all routine items. Confirm the comp item (`Jordan Patel merit +9%`) is excluded, open it, read the guardrail, and approve it individually with the justification acknowledged.

## Module 2 — Delegation (20 min)

Going on leave? Delegate your approval authority:

- Delegations are **time-boxed, 30 days maximum** — longer absences need a new delegation or an org change.
- **A delegate can never approve their own request** — self-approval is blocked at the policy layer even if routing sends it to them.
- Delegated decisions are audit-stamped with both identities ("decided by X as delegate for Y").

**Exercise 2.1** — Create a 2-week delegation to a peer. Verify (in the demo data) that the delegate's own pending PTO request does *not* appear as approvable by them.

## Module 3 — Team Time & Absence (20 min)

- **Team calendar** shows who's out when — days only, never reasons.
- **Timesheet exceptions** (missed punches, midnight-spanning shifts, DST anomalies) arrive as approval items with the computed resolution attached; you approve the *result*, the rules engine did the math.
- **Locked periods:** once payroll locks a week, changes flow as **retro deltas** — you'll see a pair (original + delta) rather than an edited row. This is correct behavior, not a bug.

## Module 4 — Compensation Cycle (45 min)

Open **Comp Cycle** during a cycle window (the demo has FY26 open).

- **Your population is a frozen snapshot** — hires/transfers after the freeze don't shift your budget mid-cycle.
- **Inline merit entry:** type the % or amount; the **live budget bar** updates as you type. Exceeding budget blocks submission, not entry — you can model freely.
- **Guideline matrix:** each worker shows a suggested range based on position-in-range (and rating where the company uses ratings). Entries outside guideline require a **written justification** — it travels with the approval and is visible to comp partners.
- **FX is locked per cycle:** cross-currency budgets use the cycle's locked rate; variance from rate drift is reported separately, never silently absorbed.
- **Conflict-of-interest routing:** you cannot effectively recommend for yourself; a manager's own line routes **skip-level** automatically.
- **Expat/dual-currency workers** show home & host figures — the split is informational; enter one recommendation.

**Exercise 4.1** — Enter merit for the demo team staying within budget, take one worker deliberately out of guideline, write its justification, submit, and trace where the out-of-guideline line routes.

## Module 5 — Recruiting Pipeline (30 min)

Open **Recruiting** (requisitions where you're hiring manager).

- **Stage flows are configured, not improvised** — candidates move through defined stages; every disposition uses the standard taxonomy (OFCCP-compliant where applicable).
- **AI rank-and-explain is advisory only:** the model orders candidates *with reasons you can read*. It has **no code path to reject anyone** — `reject()` literally refuses AI actors. You decide; the taxonomy records why.
- **Deterministic knockouts** (work authorization, license) are rule-based screens — visible as rules, not AI judgment.
- **Offers are versioned:** each revision is a new version in a chain; comp validates against the range before an offer can go out.
- **Do-not-rehire flags** are visible only with a specific permission (`candidate.read-dnr`) — absence of the flag on your screen doesn't mean absence of the flag.

**Exercise 5.1** — Advance a candidate one stage, record a disposition for another using the taxonomy, and locate the AI ranking explanation. Try to find a "reject" action attributable to the AI (you won't).

## Module 6 — Team Analytics & Talent (25 min)

- **Team analytics** (headcount, turnover, span) are scoped to your org subtree by the central policy engine — the same numbers a report or API would give you.
- **Small-group suppression:** any breakdown where a cell drops below n=5 is suppressed — including **complementary suppression** (a second cell is hidden so you can't subtract to reconstruct the first). A suppressed cell is a privacy feature working, not missing data.
- **9-box / talent review** (if invited as a rater): every placement requires a **written rationale**; re-placements append to an immutable lineage — the session minutes show the full decision history, and nothing is ever edited in place.

## Module 7 — Manager Do-Nots (10 min)

| Never | Because |
|---|---|
| Share your login to "help" a delegate | Delegation exists; sharing breaks the audit chain attribution |
| Screenshot comp data into email/chat | T2 data leaves the audited boundary; use in-app sharing |
| Ask the copilot for a teammate's protected data | It will refuse — it inherits *your* permissions, and the attempt is logged like any access |
| Pressure a recruiter to bypass disposition codes | The taxonomy is your legal defense in an audit |

---

## Competency Checklist (sign-off)

- [ ] Clears an inbox using bulk approve; handles a bulk-barred comp item correctly
- [ ] Creates a compliant delegation and explains the self-approval block
- [ ] Explains a retro delta pair on a locked timesheet
- [ ] Completes a comp worksheet within budget incl. one justified out-of-guideline entry
- [ ] Explains why their own comp line routed skip-level
- [ ] Advances/dispositions candidates; explains why AI cannot reject
- [ ] Interprets a suppressed analytics cell correctly

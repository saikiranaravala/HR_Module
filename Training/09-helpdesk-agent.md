# Training 09 — Help Desk / Service Delivery Agent

**Audience:** tier-1/2 HR case agents (`case-agent` role; ER investigators additionally need the T3 add-on below). **Duration:** 1 day. **Prerequisites:** Training 01.

## Learning Objectives

Work the case queue within SLA; use note visibility correctly; handle copilot handoffs; recognize and route the special categories (ER, legal hold, alumni, fraud interlock); keep the knowledge base healthy; operate strictly inside your data boundary.

---

## Module 1 — How Cases Reach You (45 min)

- **Routing is a decision table** (`case-routing` ruleset): category + population → your queue, with an SLA attached. You don't choose what you see; the table does — miscategorized case? Recategorize and it re-routes, audited.
- **Three arrival paths:** worker-created (form), **copilot handoff** (the AI escalates when uncertain, when sources contradict, or on request — the transcript arrives attached; *read it first*, the worker already explained once and hates repeating), and system-created (e.g., post-start adverse background finding auto-escalates to the ER queue).
- **SLA discipline:** the clock and breach state are visible on every case. Reassignments don't reset the clock.

**Exercise 1.1** — Work the demo queue: take a copilot-handoff case, confirm the transcript answers half your questions, resolve within SLA.

## Module 2 — Notes & Visibility (30 min)

Every note has an explicit visibility level:

| Level | Who sees it | Use for |
|---|---|---|
| Worker-visible | The worker + agents | Status updates, answers, requests for documents |
| Internal | Agents on the queue | Coordination, verification steps |
| Restricted (ER) | ER investigators only | Investigation content |

Rules: write worker-visible notes *for the worker's eyes* (they read them verbatim); never paste T2/T3 data (salary figures, national IDs, health details) into notes at a broader visibility than the source data; when in doubt, reference ("see comp record") rather than copy.

## Module 3 — Special Categories (60 min)

| Category | What you must know |
|---|---|
| **ER cases (T3)** | Segregated to `er-investigator` role. If you glimpse one mis-routed, route it and stop reading — **every read is audit-logged**, and "I was curious" is a finding. Never discuss ER content in general notes |
| **Legal hold** | A worker/division under hold freezes changes; transactions bounce with the hold reference. Do not help a worker "work around" a freeze — explain, and route questions to the hold's counsel contact |
| **Alumni** | Terminated workers keep scoped, time-boxed grants (payslips, tax docs). An alumnus asking for more than their grant covers → identity-verify and route to HR ops; never extend access yourself |
| **Bank-change fraud interlock** | A worker's bank change triggers verification + multi-channel notification. Calls saying "cancel that alert, it was me" get identity verification *through the defined flow* — social-engineering attempts target exactly you |
| **Delegations** | "Why can't I approve X?" — check delegation window (30-day cap) and the self-approval block before raising a defect |

## Module 4 — The Copilot Is Your Junior Colleague (30 min)

- It answers from the KB, **population-scoped** — a Germany worker gets German policy. If a worker reports a wrong-country answer, that's a sev-worthy escalation (retrieval scoping), not a shrug.
- It inherits the *worker's* permissions — it cannot leak what the worker couldn't see. It never approves, rates, or rejects.
- **You are the quality feedback loop:** wrong copilot answers almost always trace to stale KB articles. When you correct one in a case, flag the article — that's Module 5.

## Module 5 — Knowledge Base Hygiene (30 min)

- Articles pass a **legal-review gate** before publish; drafts are invisible to the copilot.
- **12-month staleness alerts** feed a review queue — stale articles are the top cause of bad answers; treat the queue as production maintenance, not busywork.
- Write for retrieval: one topic per article, country/population tags correct (they drive copilot scoping), effective dates on policy content.
- **Deflection is measured honestly** — a case reopened within 72h of copilot "resolution" counts as *not deflected*. Good articles, not optimistic closure, move the number.

---

## Competency Checklist (sign-off)

- [ ] Works a queue to resolution within SLA, including a copilot handoff
- [ ] Uses all three note-visibility levels appropriately in one case
- [ ] Correctly handles a mis-routed ER case (route, stop, no browsing)
- [ ] Explains legal hold, alumni scope, and the bank interlock to a caller
- [ ] Flags a stale KB article from a case correction
- [ ] States why reopened cases don't count as deflected

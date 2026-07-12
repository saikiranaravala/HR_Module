# Meridian Training Curriculum — Index

Training documentation for every persona that touches Project Meridian. Each document is a self-contained curriculum: audience, prerequisites, learning objectives, hands-on modules with exercises against the demo environment, and a competency checklist that gates sign-off.

## Persona → Document Map

| # | Document | Persona | Typical background | Duration |
|---|---|---|---|---|
| 01 | [End User — Employee](01-end-user-employee.md) | All employees (ESS) | None assumed | 2 h |
| 02 | [End User — Manager](02-end-user-manager.md) | People managers (MSS) | Doc 01 | 3 h |
| 03 | [Super User / HR Administrator](03-super-user-hr-admin.md) | HR ops, payroll admins, benefits admins | Docs 01–02 | 3 days |
| 04 | [Functional Consultant](04-functional-consultant.md) | Implementation & configuration consultants | HCM domain experience | 5 days |
| 05 | [Technical Consultant / Developer](05-technical-consultant.md) | Engineers extending the platform | Python, SQL, REST | 5 days |
| 06 | [DevOps / Platform Engineer](06-devops-installation.md) | Infra, deployment, CI/CD, installation | PostgreSQL, CI, cloud basics | 2 days |
| 07 | [Maintenance & Operations](07-maintenance-operations.md) | DBAs, application support (run/operate) | Doc 06 | 2 days |
| 08 | [Change Management Lead](08-change-management.md) | Adoption, communications, training delivery | Change/comm background | 2 days |
| 09 | [Help Desk / Service Delivery Agent](09-helpdesk-agent.md) | Tier-1/2 HR case agents | Doc 01 | 1 day |
| 10 | [Security & Compliance Officer](10-security-compliance.md) | InfoSec, privacy, audit, works councils | Security/privacy background | 2 days |
| 11 | [Data Migration Specialist](11-data-migration.md) | PeopleSoft extraction & cutover team | PS data model, SQL | 3 days |
| 12 | [Scenario Walkthroughs — Employee](12-scenarios-employee.md) | All employees (screenshot-per-step) | None | 1.5 h |
| 13 | [Scenario Walkthroughs — Manager](13-scenarios-manager.md) | People managers (screenshot-per-step) | Doc 12 | 1.5 h |
| 14 | [Scenario Walkthroughs — Administrator](14-scenarios-admin.md) | HR ops (screenshot-per-step) | Doc 13 | 1 h |

**Docs 12–14 are the visual companions** to 01–03: every scenario is walked step by step with a real screenshot of each state (45 images in `screenshots/`, regenerated from the live demo UI by `screenshots/_capture.mjs`). Use them for classroom projection, self-paced learning, and as the base for localized decks.

## Learning Paths

```
Employee (01)
   └─► Manager (02)
          └─► Super User (03) ──► Help Desk (09)
Consultant tracks:   Functional (04)   Technical (05)
Platform tracks:     DevOps (06) ──► Maintenance (07)
Governance tracks:   Change Mgmt (08)   Security & Compliance (10)
Program track:       Data Migration (11)
```

- **Go-live minimum:** every employee completes 01; every manager 01+02; at least two named super users per country complete 03 before their wave cuts over.
- **Certification:** each doc ends with a competency checklist. A persona is "certified" when a super user or consultant observes them completing every checklist item unaided in the demo environment.

## The Demo Environment (used by all courses)

All hands-on exercises run against the local stack (see [Deploy-local.md](../Deploy-local.md)) or the cloud stack ([Deploy-Render.md](../Deploy-Render.md)) with the demo seed dataset loaded (`SQL/run_all.sql`).

| Element | Value |
|---|---|
| UI | `http://localhost:5173` (or the Render static-site URL) |
| API / Swagger | `http://127.0.0.1:8000/docs` (or the Render API URL) |
| Demo personas | **Avery Quinn** (Employee Self Service), **Morgan Lee** (Manager Self Service), **Sam Rivera** (Workforce Administrator) — switch via the homepage selector or the avatar menu |
| Demo cast | 9 coherent synthetic workers spanning every module's features (see `SQL/README`) |
| Reset | `psql … -f SQL/00_reset.sql` then `-f SQL/run_all.sql` (idempotent) |

**All demo data is synthetic.** No real names, national IDs (900-xx reserved SSN ranges only), or bank details exist anywhere in the system. Trainers must never import production data into training environments (Invariant #8).

## House Rules Reflected in Every Course

These platform behaviors appear across all curricula because trainees will encounter them immediately:

1. **Effective dating everywhere** — nothing about a person is "just updated"; every change has an effective date, a sequence, an action/reason, and an audit trail.
2. **One policy brain** — if you can't see something, neither can a report, an API call, or the AI copilot. There is no side door, by design.
3. **Sensitive reads are logged** — viewing compensation, national IDs, banking (T2) or health-adjacent/ER/succession data (T3) writes an audit event with your identity. This is normal and visible in the UI.
4. **AI drafts, humans decide** — the copilot answers questions and drafts documents; it never approves, rates, rejects, or commits anything touching money, employment status, or access.
5. **Config, not code** — business rules change through versioned decision tables and workflow definitions, never through scripts.

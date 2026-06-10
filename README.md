# Project Meridian — AI-Native HCM Platform

**Mission:** Replace Oracle PeopleSoft HCM with a cloud-native, AI-native Human Capital Management platform serving **50,000+ employees globally**, cut over via a **6–12 month parallel run** with penny-perfect payroll gates.

> Status: Specification phase complete · Foundation phase pending kickoff
> Owner: HCM Platform Program · Last updated: June 2026

---

## What is Meridian?

A full-suite HCM platform — Core HR, Time & Labor, Payroll orchestration, Benefits, Compensation, Recruiting, Performance, Learning, Succession, ESS/MSS, and Analytics — built on three strategic bets:

1. **Payroll is orchestration, not calculation.** A Payroll Integration Hub drives certified local providers (ADP, etc.) behind one canonical data contract. Meridian owns every input and result; providers own statutory gross-to-net.
2. **AI-native, not AI-added.** Copilots, agents (LangGraph), and population-scoped retrieval (vectorless-first, hierarchical index-tree) are platform services with centralized governance — EU AI Act and NYC LL144 compliant by design.
3. **The parallel run is the trust mechanism.** PeopleSoft stays authoritative until each country posts three consecutive $0.00-net-variance payroll cycles. Rollback is rehearsed until it's unneeded.

## Documentation Map

| Document | Purpose |
|---|---|
| `PRD-Meridian-HCM.md` | **Master PRD** — vision, goals, module summaries, roadmap, risks |
| `00-INDEX.md` | Deep-dive library index + cross-cutting decision dependencies |
| `01-core-hr.md` … `16-migration.md` | **16 domain deep-dives** — data models, workflows, acceptance criteria, edge-case registers, events/APIs |
| `CLAUDE.md` | AI-assistant working instructions for this repo (conventions, invariants, guardrails) |

**Reading order for newcomers:** Master PRD → 00-INDEX → 15 (architecture) → 01 (Core HR) → 03 (Payroll Hub) → your domain.

## Architecture at a Glance

- **Services:** bounded contexts (Person, Employment, Time, Payroll Hub, Benefits, Comp, Talent, Service Delivery, Workflow, AI Gateway, Analytics) on Kubernetes (EKS), GitOps, Terraform.
- **Data:** PostgreSQL per service with a shared **temporal-data platform service** (effective date + sequence + as-of querying — the single most important consistency layer); Kafka event backbone (CloudEvents); Iceberg lakehouse; WORM storage for payslips/audit.
- **Security:** central policy service (RBAC + ABAC, sensitivity tiers T0–T3) serving UI, APIs, analytics, and AI tool scopes identically; immutable hash-chained audit incl. read-logging on sensitive data; EU data plane for residency.
- **Extensibility:** configuration-only (workflow designer, decision-table rules engine, governed custom fields). **No code forks. No server-side scripting hooks. Ever.**

## Non-Negotiable Program Gates

1. ≥ 99.95% field-match on critical data before any population enters parallel run.
2. Three consecutive penny-perfect payroll cycles per country before authority transfer.
3. Country compliance pack certified before that country's pilot.
4. AI use cases registered, risk-classified, and governance-approved before production.
5. Works-council consultation complete before a country's pilot — not before its cutover.

## Open Decisions (gating Foundation exit)

Payroll provider RFP · performance ratings philosophy · ATS/LMS build-vs-buy · IN/CN data-residency rulings · works-council inventory. Details in `00-INDEX.md`.

## Glossary

**CPDC** Canonical Payroll Data Contract · **JML** Joiner-Mover-Leaver · **OE** Open Enrollment · **EFFDT/EFFSEQ** Effective date/sequence (temporal model) · **Wave** A country/region cutover cohort · **Hypercare** Post-cutover intensive support period · **Country pack** Versioned statutory configuration content per jurisdiction

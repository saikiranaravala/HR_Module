# Project Meridian — Deep-Dive PRD Library (Index)
Companion to the master PRD (PRD-Meridian-HCM.md). Sixteen domain PRDs, each covering: mission & metrics, detailed requirements with acceptance criteria, data model, workflows, events/APIs, edge-case register, and open questions.

| # | PRD | Domain | Phase anchor |
|---|---|---|---|
| 01 | 01-core-hr.md | Core HR & Workforce Administration | Foundation (P0) |
| 02 | 02-time-labor.md | Time & Labor + Absence | Operational core (P0) |
| 03 | 03-payroll-hub.md | Payroll Integration Hub | Operational core (P0) |
| 04 | 04-benefits.md | Benefits Administration | Operational core (P0) |
| 05 | 05-compensation.md | Compensation Planning | Talent suite (P1) |
| 06 | 06-recruiting.md | Recruiting & Onboarding (ATS) | Talent suite (P1) |
| 07 | 07-performance.md | Performance Management | Talent suite (P1) |
| 08 | 08-learning.md | Learning & Development (LMS) | Compliance engine P0; rest P1 |
| 09 | 09-succession.md | Succession & Career Planning | Talent suite (P1) |
| 10 | 10-ess-mss.md | ESS/MSS + HR Service Delivery | Operational core (P0) |
| 11 | 11-analytics.md | Workforce Analytics & Reporting | Foundation→P1 |
| 12 | 12-platform.md | Workflow, Rules & Extensibility | Foundation (P0) |
| 13 | 13-integration.md | Integration Architecture | Foundation (P0) |
| 14 | 14-ai-layer.md | AI-Native Capability Layer | Foundation (P0) |
| 15 | 15-technical-architecture.md | Tech, Security & Privacy | Foundation (P0) |
| 16 | 16-migration.md | Migration & Parallel Run | Program-long |

**Cross-cutting decision dependencies (resolve first):**
1. Payroll provider RFP (gates 03 adapters, 16 wave map) — month 0–2.
2. Performance philosophy: ratings/ratingless (gates 07 templates, 05 guidelines, 09 9-box) — month 4 workshop.
3. ATS/LMS build-vs-buy confirmation (gates 06/08 scope) — Foundation exit.
4. Data residency rulings: EU plane confirmed; IN DPDP and CN PIPL assessments (gates 15 deployment topology) — month 1 legal study.
5. Works-council/union consultation inventory (gates 16 wave sequencing) — month 1–3.

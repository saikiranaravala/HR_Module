# Deep-Dive PRD 11 — Workforce Analytics & Reporting
*Project Meridian | Depends on: all modules via event stream, 15-Tech lakehouse | Serves: every persona + external BI*

## 1. Mission & Success Metrics
One governed truth for workforce data: operational reports for the many, executive analytics for decisions, predictions with ethics — all under inherited security.
- Metric consistency: zero competing definitions (semantic layer is sole source; "headcount" defined once).
- Legacy rationalization: PeopleSoft report inventory dispositioned 100% (rebuild ≤ 30%, retire ≥ 60%, replace-by-dashboard rest).
- Freshness: operational data ≤ 15 min lag; certified daily snapshots by 06:00 local per region.

## 2. Data Platform
Event-streamed CDC from service stores → bronze (raw, immutable) → silver (conformed dimensional model: Worker, Assignment(SCD2 mirroring effective dating), Org, Position, PayResult, Absence, Application, Review, Enrollment facts) → gold (metric marts). Iceberg on object storage; dbt-managed transformations with tests + lineage; PII vault pattern (tokenized identifiers in analytics; re-identification only via governed service with purpose logging); residency: regional lakehouse planes mirroring TECH-10, global aggregates only above suppression thresholds.

## 3. Semantic Layer & Certified Metrics
Governed metric registry (headcount [point-in-time, FTE-weighted variants], hires, exits, turnover [annualized, regrettable split], internal mobility rate, span of control, time-to-fill, offer-accept rate, absence rate, OT %, labor cost [fully loaded from PAY employer-cost], compliance-training completion, eNPS ingest…). Each metric: definition, formula, grain, owner, change log. Exposed identically to native dashboards, Tableau/Power BI connectors (passthrough auth — row/field security from TECH-5 policy source, never re-implemented in BI), and API.

## 4. Operational Reporting
Self-service builder: certified datasets, drag-drop columns/filters, save/share within security scope, schedule + burst (deliver per-manager slices), export with watermarking + DLP tags; report catalog with ownership/review dates; **migration workstream:** PeopleSoft query/nVision inventory → usage telemetry triage → disposition board (the 60-80% retirement target from master ANLT-1) — every wave's cutover checklist includes its report disposition signoff.

## 5. Executive & Domain Analytics
Executive workforce dashboard (headcount vs. plan, movement flows Sankey, cost trends, attrition hotspots with drivers panel, DEI composition with n≥5 suppression + small-group rollups); domain packs: Talent acquisition funnel + source ROI; Performance distributions + calibration shift analysis; Comp (range penetration, budget burn, pay-equity headline indicators with privileged-deep-dive separation per 05); Time (OT cost heatmaps, WTD risk); Benefits participation/cost. Board pack generator: templated quarterly export, redaction rules enforced.

## 6. Predictive & Advanced (P2, ethics-gated)
Attrition risk: aggregate-first deployment (org-level heatmaps year one; individual scores only after 14-AI governance review, restricted tier, never visible to direct manager as a bare score), explainability mandatory, quarterly bias/stability monitoring. Workforce planning: scenario modeler (hiring plans, reorg costs, attrition assumptions → headcount/cost projections), driver-based with Finance plan import. Absence anomaly detection (pattern shifts at org level → wellbeing signal for HR, never individual discipline triggers — explicit policy).

## 7. APIs & Eventing
Metrics API (semantic-layer queries), snapshot API (as-of population extracts for auditors), reverse-ETL feeds (planning tools), data contracts for downstream consumers with schema-change notification SLAs.

## 8. Edge Cases Register
Retro transactions rewriting history (SCD2 restatement policy: facts restate, certified snapshots immutable with restatement annotations); org reorg breaking trend continuity (org-mapping bridge tables for like-for-like trending); n<5 suppression interaction with drill-down (no residual disclosure via subtraction — complementary suppression); contractor inclusion toggles per metric.

## 9. Open Questions
BI standard (Tableau vs. Power BI) — pick one for certified content. Finance plan system integration depth for workforce planning. eNPS/survey platform: integrate vs. native pulse (recommend integrate).
